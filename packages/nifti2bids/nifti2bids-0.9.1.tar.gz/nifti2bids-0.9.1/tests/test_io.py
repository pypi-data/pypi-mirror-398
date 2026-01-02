import nibabel as nib
import nifti2bids.io as bids_io


def test_compress_image(nifti_img_and_path):
    """Test for ``compress_image``."""
    _, img_path = nifti_img_and_path

    files = list(img_path.parent.glob("*"))
    assert len(files) == 1

    file = files[0]
    assert file.suffix.endswith(".nii")

    bids_io.compress_image(img_path, remove_src_file=True)

    files = list(img_path.parent.glob("*"))
    assert len(files) == 1

    file = files[0]
    assert file.suffixes == [".nii", ".gz"]


def test_load_nifti(nifti_img_and_path):
    """Test for ``load_nifti``."""
    img, img_path = nifti_img_and_path
    assert isinstance(bids_io.load_nifti(img), nib.nifti1.Nifti1Image)
    assert isinstance(bids_io.load_nifti(img_path), nib.nifti1.Nifti1Image)


def test_glob_contents(nifti_img_and_path):
    """Test for ``glob_contents``"""
    _, img_path = nifti_img_and_path
    files = bids_io.glob_contents(img_path.parent, pattern="*.nii")
    assert len(files) == 1


def test_get_nifti_header(nifti_img_and_path):
    """Test for ``get_nifti_header``."""
    img, _ = nifti_img_and_path
    assert isinstance(bids_io.get_nifti_header(img), nib.nifti1.Nifti1Header)


def test_get_nifti_affine(nifti_img_and_path):
    """Test for ``get_nifti_affine``."""
    img, _ = nifti_img_and_path
    assert bids_io.get_nifti_affine(img).shape == (4, 4)
