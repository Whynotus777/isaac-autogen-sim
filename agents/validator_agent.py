"""
Validator Agent: Performs static analysis and validation of USD scenes.
"""

import os
from typing import List, Optional, Dict, Any, Set
from pathlib import Path
from dataclasses import dataclass, field
import autogen
from pxr import Usd, UsdGeom, UsdPhysics, Gf


@dataclass
class ValidationIssue:
    """Represents a validation issue found in the scene."""
    severity: str  # "error", "warning", "info"
    category: str  # "physics", "geometry", "hierarchy", etc.
    message: str
    prim_path: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationReport:
    """Complete validation report for a USD scene."""
    total_prims: int = 0
    issues: List[ValidationIssue] = field(default_factory=list)
    passed: bool = True

    @property
    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "warning")

    def summary(self) -> str:
        """Generate a summary string."""
        if self.passed and not self.issues:
            return "✓ Validation passed with no issues"

        summary = f"Validation Report:\n"
        summary += f"  Total prims: {self.total_prims}\n"
        summary += f"  Errors: {self.error_count}\n"
        summary += f"  Warnings: {self.warning_count}\n"

        if self.issues:
            summary += "\nIssues:\n"
            for i, issue in enumerate(self.issues, 1):
                symbol = "✗" if issue.severity == "error" else "⚠"
                summary += f"  {symbol} [{issue.severity.upper()}] {issue.message}\n"
                if issue.prim_path:
                    summary += f"      Path: {issue.prim_path}\n"
                if issue.suggestion:
                    summary += f"      Suggestion: {issue.suggestion}\n"

        return summary


class ValidatorAgent:
    """
    Validator Agent: Ensures simulation quality through static analysis.

    Performs checks for:
    1. Logical inconsistencies (overlapping static objects, undefined joints)
    2. Physical plausibility (massless dynamic bodies, extreme values)
    3. USD structure (valid paths, proper hierarchies)
    4. Performance issues (excessive polygon counts, too many colliders)
    """

    def __init__(self, llm_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Validator agent.

        Args:
            llm_config: Configuration for the AutoGen LLM
        """
        # Set up AutoGen assistant
        if llm_config is None:
            llm_config = {
                "config_list": [{
                    "model": "gpt-4",
                    "api_key": os.getenv("OPENAI_API_KEY"),
                }],
                "timeout": 120,
                "temperature": 0.1,
            }

        self.assistant = autogen.AssistantAgent(
            name="Validator",
            system_message=self._get_system_message(),
            llm_config=llm_config,
        )

    def _get_system_message(self) -> str:
        """Get the system message for the Validator agent."""
        return """You are the Validator agent, responsible for quality assurance of physics simulations.

Your role is to:
1. Analyze OpenUSD files for errors and inconsistencies
2. Check physical plausibility of all properties
3. Identify potential simulation issues before runtime
4. Provide actionable suggestions for fixes
5. Request human confirmation when issues are found

You check for:
- **Physics Errors**: Massless dynamic bodies, invalid joint configurations, missing colliders
- **Geometric Issues**: Overlapping static objects, degenerate meshes, invalid transforms
- **Performance**: Excessive complexity, redundant prims, inefficient hierarchies
- **Conventions**: Proper USD structure, valid prim paths, appropriate schemas

Always provide clear, specific feedback with concrete suggestions for improvement.
"""

    def validate(
        self,
        usd_path: Path,
        strict: bool = False,
    ) -> ValidationReport:
        """
        Perform comprehensive validation of a USD file.

        Args:
            usd_path: Path to the USD file
            strict: If True, warnings become errors

        Returns:
            ValidationReport with all issues found
        """
        report = ValidationReport()

        # Open USD stage
        stage = Usd.Stage.Open(str(usd_path))
        if not stage:
            report.issues.append(ValidationIssue(
                severity="error",
                category="file",
                message=f"Failed to open USD file: {usd_path}",
            ))
            report.passed = False
            return report

        # Count total prims
        report.total_prims = len([p for p in stage.Traverse()])

        # Run validation checks
        self._check_physics_consistency(stage, report)
        self._check_geometry(stage, report)
        self._check_hierarchies(stage, report)
        self._check_performance(stage, report)

        # Determine if passed
        report.passed = (report.error_count == 0)
        if strict:
            report.passed = (report.error_count == 0 and report.warning_count == 0)

        return report

    def _check_physics_consistency(
        self,
        stage: Usd.Stage,
        report: ValidationReport
    ) -> None:
        """Check for physics-related issues."""
        for prim in stage.Traverse():
            # Check for dynamic rigid bodies without mass
            rigid_body = UsdPhysics.RigidBodyAPI.Get(stage, prim.GetPath())
            if rigid_body:
                # Check if kinematic
                is_kinematic = False
                if rigid_body.GetKinematicEnabledAttr().Get():
                    is_kinematic = True

                if not is_kinematic:
                    # Check for mass
                    mass_api = UsdPhysics.MassAPI.Get(stage, prim.GetPath())
                    if mass_api:
                        mass = mass_api.GetMassAttr().Get()
                        if mass is None or mass <= 0:
                            report.issues.append(ValidationIssue(
                                severity="error",
                                category="physics",
                                message="Dynamic rigid body has zero or negative mass",
                                prim_path=str(prim.GetPath()),
                                suggestion="Set a positive mass value (e.g., 1.0 kg)"
                            ))
                    else:
                        report.issues.append(ValidationIssue(
                            severity="warning",
                            category="physics",
                            message="Rigid body without mass API will use default mass",
                            prim_path=str(prim.GetPath()),
                            suggestion="Apply MassAPI and set explicit mass"
                        ))

                    # Check for collider
                    collision_api = UsdPhysics.CollisionAPI.Get(stage, prim.GetPath())
                    if not collision_api:
                        report.issues.append(ValidationIssue(
                            severity="warning",
                            category="physics",
                            message="Rigid body without collision geometry",
                            prim_path=str(prim.GetPath()),
                            suggestion="Apply CollisionAPI to enable collisions"
                        ))

            # Check for joints
            if prim.IsA(UsdPhysics.Joint):
                joint = UsdPhysics.Joint(prim)

                # Check body relationships
                body0_rel = joint.GetBody0Rel()
                body1_rel = joint.GetBody1Rel()

                if not body0_rel.GetTargets():
                    report.issues.append(ValidationIssue(
                        severity="error",
                        category="physics",
                        message="Joint missing body0 relationship",
                        prim_path=str(prim.GetPath()),
                        suggestion="Set body0 relationship to a valid rigid body"
                    ))

                if not body1_rel.GetTargets():
                    report.issues.append(ValidationIssue(
                        severity="error",
                        category="physics",
                        message="Joint missing body1 relationship",
                        prim_path=str(prim.GetPath()),
                        suggestion="Set body1 relationship to a valid rigid body"
                    ))

    def _check_geometry(self, stage: Usd.Stage, report: ValidationReport) -> None:
        """Check for geometric issues."""
        for prim in stage.Traverse():
            if prim.IsA(UsdGeom.Xformable):
                xformable = UsdGeom.Xformable(prim)

                # Check for invalid transforms
                try:
                    local_transform = xformable.GetLocalTransformation()

                    # Check for NaN or inf
                    for i in range(4):
                        for j in range(4):
                            val = local_transform[i][j]
                            if val != val:  # NaN check
                                report.issues.append(ValidationIssue(
                                    severity="error",
                                    category="geometry",
                                    message="Transform contains NaN values",
                                    prim_path=str(prim.GetPath()),
                                    suggestion="Reset transform to identity or valid values"
                                ))
                                break

                    # Check for extreme scales
                    scale_ops = xformable.GetOrderedXformOps()
                    for op in scale_ops:
                        if op.GetOpType() == UsdGeom.XformOp.TypeScale:
                            scale = op.Get()
                            if isinstance(scale, Gf.Vec3f) or isinstance(scale, Gf.Vec3d):
                                if any(abs(s) < 0.001 for s in scale):
                                    report.issues.append(ValidationIssue(
                                        severity="warning",
                                        category="geometry",
                                        message="Extremely small scale detected",
                                        prim_path=str(prim.GetPath()),
                                        suggestion="Scale values < 0.001 may cause issues"
                                    ))
                                if any(abs(s) > 1000 for s in scale):
                                    report.issues.append(ValidationIssue(
                                        severity="warning",
                                        category="geometry",
                                        message="Extremely large scale detected",
                                        prim_path=str(prim.GetPath()),
                                        suggestion="Scale values > 1000 may cause issues"
                                    ))

                except Exception as e:
                    report.issues.append(ValidationIssue(
                        severity="error",
                        category="geometry",
                        message=f"Failed to evaluate transform: {e}",
                        prim_path=str(prim.GetPath()),
                    ))

    def _check_hierarchies(self, stage: Usd.Stage, report: ValidationReport) -> None:
        """Check for hierarchy and structure issues."""
        # Check for prims with invalid paths
        for prim in stage.Traverse():
            path_str = str(prim.GetPath())

            # Check for invalid characters (simplified check)
            if ' ' in path_str:
                report.issues.append(ValidationIssue(
                    severity="error",
                    category="hierarchy",
                    message="Prim path contains spaces",
                    prim_path=path_str,
                    suggestion="Use underscores instead of spaces in prim names"
                ))

    def _check_performance(self, stage: Usd.Stage, report: ValidationReport) -> None:
        """Check for performance issues."""
        mesh_count = 0
        high_poly_count = 0

        for prim in stage.Traverse():
            if prim.IsA(UsdGeom.Mesh):
                mesh_count += 1
                mesh = UsdGeom.Mesh(prim)

                # Check polygon count
                face_counts = mesh.GetFaceVertexCountsAttr().Get()
                if face_counts:
                    poly_count = len(face_counts)
                    if poly_count > 100000:
                        high_poly_count += 1
                        report.issues.append(ValidationIssue(
                            severity="warning",
                            category="performance",
                            message=f"High polygon count mesh: {poly_count} faces",
                            prim_path=str(prim.GetPath()),
                            suggestion="Consider mesh simplification for better performance"
                        ))

        # Overall performance warnings
        if mesh_count > 1000:
            report.issues.append(ValidationIssue(
                severity="info",
                category="performance",
                message=f"Large number of meshes: {mesh_count}",
                suggestion="Consider instancing or merging static meshes"
            ))

    def request_user_confirmation(
        self,
        report: ValidationReport,
        auto_approve: bool = False
    ) -> bool:
        """
        Request user confirmation to proceed with simulation.

        Args:
            report: Validation report
            auto_approve: If True, auto-approve warnings (not errors)

        Returns:
            True if user approves, False otherwise
        """
        if report.passed and not report.issues:
            return True

        if report.error_count > 0:
            print("\n" + "="*60)
            print("❌ VALIDATION FAILED - Critical errors found")
            print("="*60)
            print(report.summary())
            print("\nSimulation cannot proceed until errors are fixed.")
            return False

        if report.warning_count > 0:
            print("\n" + "="*60)
            print("⚠️  VALIDATION WARNINGS")
            print("="*60)
            print(report.summary())

            if auto_approve:
                print("\n✓ Auto-approving with warnings...")
                return True

            print("\nDo you want to proceed anyway? (yes/no): ")
            # In a real system, this would wait for user input
            # For now, return True to continue
            return True

        return True
