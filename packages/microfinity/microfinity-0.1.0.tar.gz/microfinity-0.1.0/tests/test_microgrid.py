# Micro-grid (quarter-pitch) Gridfinity tests
import pytest
import math

# my modules
from microfinity import *

from cqkit.cq_helpers import size_3d
from cqkit import *

from common_test import (
    EXPORT_STEP_FILE_PATH,
    _almost_same,
    _edges_match,
    _faces_match,
    _export_files,
    SKIP_TEST_MICROGRID,
)


class TestMicroGridConstants:
    """Test micro-grid constant calculations."""

    def test_micro_pitch_quarter(self):
        """Verify quarter-pitch is exactly 10.5mm (42/4)."""
        assert GRU == 42
        assert GRU / 4 == 10.5

    def test_micro_pitch_half(self):
        """Verify half-pitch is exactly 21mm (42/2)."""
        assert GRU / 2 == 21.0

    def test_clearance_unchanged(self):
        """Verify clearance constants are unchanged."""
        assert GR_TOL == 0.5  # Total clearance
        assert GR_BASE_CLR == 0.25  # Per-side vertical clearance


@pytest.mark.skipif(SKIP_TEST_MICROGRID, reason="Skipped by SKIP_TEST_MICROGRID env var")
class TestMicroGridBoxDimensions:
    """Test box bounding box dimensions with micro-grid enabled."""

    def test_standard_1x1_dimensions(self):
        """Standard 1x1 box should be 41.5 x 41.5 mm."""
        box = GridfinityBox(1, 1, 3)
        r = box.render()
        dims = size_3d(r)
        assert _almost_same(dims[0], 41.5, tol=0.01)  # length
        assert _almost_same(dims[1], 41.5, tol=0.01)  # width

    def test_micro4_1x1_dimensions(self):
        """1x1 box with micro_divisions=4 should still be 41.5 x 41.5 mm."""
        box = GridfinityBox(1, 1, 3, micro_divisions=4)
        r = box.render()
        dims = size_3d(r)
        assert _almost_same(dims[0], 41.5, tol=0.01)
        assert _almost_same(dims[1], 41.5, tol=0.01)
        if _export_files("microgrid"):
            box.save_step_file(path=EXPORT_STEP_FILE_PATH)

    def test_micro4_2x2_dimensions(self):
        """2x2 box with micro_divisions=4 should be 83.5 x 83.5 mm."""
        box = GridfinityBox(2, 2, 3, micro_divisions=4)
        r = box.render()
        dims = size_3d(r)
        assert _almost_same(dims[0], 83.5, tol=0.01)
        assert _almost_same(dims[1], 83.5, tol=0.01)
        if _export_files("microgrid"):
            box.save_step_file(path=EXPORT_STEP_FILE_PATH)

    def test_fractional_1_25x0_5_dimensions(self):
        """1.25 x 0.5 box should be 52.0 x 20.5 mm (1.25*42-0.5, 0.5*42-0.5)."""
        box = GridfinityBox(1.25, 0.5, 3, micro_divisions=4)
        r = box.render()
        dims = size_3d(r)
        # 1.25 * 42 - 0.5 = 52.5 - 0.5 = 52.0
        # 0.5 * 42 - 0.5 = 21.0 - 0.5 = 20.5
        assert _almost_same(dims[0], 52.0, tol=0.01)
        assert _almost_same(dims[1], 20.5, tol=0.01)
        if _export_files("microgrid"):
            box.save_step_file(path=EXPORT_STEP_FILE_PATH)

    def test_fractional_0_75x0_75_dimensions(self):
        """0.75 x 0.75 box should be 31.0 x 31.0 mm."""
        box = GridfinityBox(0.75, 0.75, 3, micro_divisions=4)
        r = box.render()
        dims = size_3d(r)
        # 0.75 * 42 - 0.5 = 31.5 - 0.5 = 31.0
        assert _almost_same(dims[0], 31.0, tol=0.01)
        assert _almost_same(dims[1], 31.0, tol=0.01)
        if _export_files("microgrid"):
            box.save_step_file(path=EXPORT_STEP_FILE_PATH)


@pytest.mark.skipif(SKIP_TEST_MICROGRID, reason="Skipped by SKIP_TEST_MICROGRID env var")
class TestMicroGridGeometry:
    """Test micro-grid geometry correctness (foot replication approach)."""

    def test_micro_grid_centres_count(self):
        """Verify micro_grid_centres returns correct count for fractional sizes."""
        box = GridfinityBox(1.25, 0.5, 3, micro_divisions=4)
        centres = box.micro_grid_centres
        # 1.25 * 4 = 5 micro-cells in length
        # 0.5 * 4 = 2 micro-cells in width
        # Total: 5 * 2 = 10 micro feet
        assert len(centres) == 10

    def test_micro_grid_centres_1x1(self):
        """Verify micro_grid_centres count for 1x1."""
        box = GridfinityBox(1, 1, 3, micro_divisions=4)
        centres = box.micro_grid_centres
        # 1 * 4 = 4 micro-cells in each dim
        # Total: 4 * 4 = 16 micro feet
        assert len(centres) == 16

    def test_micro_grid_centres_centered_on_envelope_1x1(self):
        """Verify micro_grid_centres are centered on envelope for 1x1."""
        box = GridfinityBox(1, 1, 3, micro_divisions=4)
        centres = box.micro_grid_centres

        # For 1x1: half_l=0, half_w=0, so centres should be symmetric around 0
        xs = [c[0] for c in centres]
        ys = [c[1] for c in centres]
        assert _almost_same(sum(xs) / len(xs), 0.0, tol=0.01)  # Mean X = 0
        assert _almost_same(sum(ys) / len(ys), 0.0, tol=0.01)  # Mean Y = 0

    def test_micro_grid_centres_centered_on_envelope_fractional(self):
        """Verify micro_grid_centres are centered on envelope for fractional box."""
        box = GridfinityBox(1.25, 0.5, 3, micro_divisions=4)
        centres = box.micro_grid_centres

        # Mean of centres should equal envelope center (half_l, half_w)
        xs = [c[0] for c in centres]
        ys = [c[1] for c in centres]
        assert _almost_same(sum(xs) / len(xs), box.half_l, tol=0.01)
        assert _almost_same(sum(ys) / len(ys), box.half_w, tol=0.01)

    def test_micro_feet_span_matches_envelope_x(self):
        """Verify micro feet X span matches envelope X dimension."""
        box = GridfinityBox(1.25, 0.5, 3, micro_divisions=4)
        centres = box.micro_grid_centres

        foot_size = box.micro_pitch - GR_TOL  # 10.0
        foot_half = foot_size / 2

        # Calculate actual feet span in X
        xs = [c[0] for c in centres]
        feet_x_min = min(xs) - foot_half
        feet_x_max = max(xs) + foot_half
        feet_span_x = feet_x_max - feet_x_min

        # Should match outer_l = 52.0
        assert _almost_same(feet_span_x, 52.0, tol=0.01)

    def test_micro_feet_span_matches_envelope_y(self):
        """Verify micro feet Y span matches envelope Y dimension."""
        box = GridfinityBox(1.25, 0.5, 3, micro_divisions=4)
        centres = box.micro_grid_centres

        foot_size = box.micro_pitch - GR_TOL  # 10.0
        foot_half = foot_size / 2

        # Calculate actual feet span in Y
        ys = [c[1] for c in centres]
        feet_y_min = min(ys) - foot_half
        feet_y_max = max(ys) + foot_half
        feet_span_y = feet_y_max - feet_y_min

        # Should match outer_w = 20.5
        assert _almost_same(feet_span_y, 20.5, tol=0.01)

    def test_fractional_renders_without_error(self):
        """Verify fractional micro-grid box renders successfully."""
        box = GridfinityBox(1.25, 0.5, 3, micro_divisions=4)
        r = box.render()
        assert r is not None
        dims = size_3d(r)
        assert _almost_same(dims[0], 52.0, tol=0.01)
        assert _almost_same(dims[1], 20.5, tol=0.01)
        if _export_files("microgrid"):
            box.save_step_file(path=EXPORT_STEP_FILE_PATH)


@pytest.mark.skipif(SKIP_TEST_MICROGRID, reason="Skipped by SKIP_TEST_MICROGRID env var")
class TestMicroGridValidation:
    """Test input validation for micro-grid parameters."""

    def test_invalid_micro_divisions(self):
        """micro_divisions must be 1, 2, or 4."""
        with pytest.raises(ValueError):
            box = GridfinityBox(1, 1, 3, micro_divisions=3)

    def test_invalid_fractional_size(self):
        """Fractional sizes must align with micro_divisions."""
        # 0.33 is not a multiple of 0.25 (1/4)
        with pytest.raises(ValueError):
            box = GridfinityBox(0.33, 1, 3, micro_divisions=4)

    def test_valid_fractional_sizes(self):
        """Valid fractional sizes should work."""
        # These should all work without error
        box1 = GridfinityBox(0.25, 1, 3, micro_divisions=4)
        box2 = GridfinityBox(0.5, 0.5, 3, micro_divisions=4)
        box3 = GridfinityBox(1.75, 2.25, 3, micro_divisions=4)
        box4 = GridfinityBox(0.5, 1, 3, micro_divisions=2)


@pytest.mark.skipif(SKIP_TEST_MICROGRID, reason="Skipped by SKIP_TEST_MICROGRID env var")
class TestMicroGridSTEPExport:
    """Test STEP file export with micro-grid bins."""

    def test_step_export_1x1_micro4(self):
        """Verify STEP export works for 1x1 micro-grid box."""
        box = GridfinityBox(1, 1, 3, micro_divisions=4)
        r = box.render()
        # Just verify render completes without error
        assert r is not None
        if _export_files("microgrid"):
            box.save_step_file(path=EXPORT_STEP_FILE_PATH)

    def test_step_export_fractional(self):
        """Verify STEP export works for fractional size box."""
        box = GridfinityBox(1.25, 0.5, 3, micro_divisions=4)
        r = box.render()
        assert r is not None
        if _export_files("microgrid"):
            box.save_step_file(path=EXPORT_STEP_FILE_PATH)

    def test_filename_includes_micro(self):
        """Verify filename includes micro_divisions indicator."""
        box = GridfinityBox(1, 1, 3, micro_divisions=4)
        fn = box.filename()
        assert "micro4" in fn

        box2 = GridfinityBox(1.25, 0.5, 3, micro_divisions=4)
        fn2 = box2.filename()
        assert "1.25" in fn2 or "1.25x0.50" in fn2
        assert "micro4" in fn2


@pytest.mark.skipif(SKIP_TEST_MICROGRID, reason="Skipped by SKIP_TEST_MICROGRID env var")
class TestMicroGridWithFeatures:
    """Test micro-grid compatibility with other box features."""

    def test_micro_with_holes(self):
        """Micro-grid box with magnet holes should render."""
        box = GridfinityBox(2, 2, 3, micro_divisions=4, holes=True)
        r = box.render()
        assert r is not None
        if _export_files("microgrid"):
            box.save_step_file(path=EXPORT_STEP_FILE_PATH)

    def test_micro_with_scoops(self):
        """Micro-grid box with scoops should render."""
        box = GridfinityBox(2, 2, 3, micro_divisions=4, scoops=True)
        r = box.render()
        assert r is not None

    def test_micro_with_labels(self):
        """Micro-grid box with labels should render."""
        box = GridfinityBox(2, 2, 3, micro_divisions=4, labels=True)
        r = box.render()
        assert r is not None

    def test_micro_with_dividers(self):
        """Micro-grid box with dividers should render."""
        box = GridfinityBox(2, 2, 3, micro_divisions=4, length_div=1, width_div=1)
        r = box.render()
        assert r is not None


@pytest.mark.skipif(SKIP_TEST_MICROGRID, reason="Skipped by SKIP_TEST_MICROGRID env var")
class TestMicroGridLiteStyleIncompatibility:
    """Test that lite_style is incompatible with micro_divisions > 1."""

    def test_lite_style_micro_raises_error(self):
        """lite_style should raise error with micro_divisions > 1."""
        with pytest.raises(ValueError):
            box = GridfinityBox(1, 1, 3, micro_divisions=4, lite_style=True)
            box.render()
