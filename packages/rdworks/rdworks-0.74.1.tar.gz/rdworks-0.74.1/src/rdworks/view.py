from io import BytesIO
from PIL import Image, ImageChops

from collections.abc import Iterable

from rdkit import Chem
from rdkit.Chem import AllChem, Draw, rdDepictor, rdMolTransforms, PeriodicTable
from rdkit.Chem.Draw import rdMolDraw2D
from rdkit.Chem.Draw import MolsMatrixToGridImage  # new in RDKit 2023.09.1
from rdkit.Geometry import Point2D

# SVG optimization
from scour.scour import scourString

# https://greglandrum.github.io/rdkit-blog/posts/2023-05-26-drawing-options-explained.html

import numpy as np


def trim_png(img: Image.Image) -> Image.Image:
    """Removes white margin around molecular drawing.

    Args:
        img (Image.Image): input PIL Image object.

    Returns:
        Image.Image: output PIL Image object.
    """
    bg = Image.new(img.mode, img.size, img.getpixel((0, 0)))
    diff = ImageChops.difference(img, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()

    if bbox:
        return img.crop(bbox)

    return img


def get_highlight_bonds(rdmol: Chem.Mol, atom_indices: list[int]) -> list[int] | None:
    """Get bond indices for bonds between atom indices.

    Args:
        rdmol (Chem.Mol): rdkit Chem.Mol object.
        atom_indices (list[int]): atom indices.

    Returns:
        list[int]: bond indices.
    """
    bond_indices = []
    for bond in rdmol.GetBonds():
        if (
            bond.GetBeginAtomIdx() in atom_indices
            and bond.GetEndAtomIdx() in atom_indices
        ):
            bond_indices.append(bond.GetIdx())

    if bond_indices:
        return bond_indices
    else:
        return None


def render_2D_mol(
    rdmol: Chem.Mol,
    moldrawer: rdMolDraw2D,
    redraw: bool = False,
    coordgen: bool = False,
    legend: str = "",
    atom_index: bool = False,
    highlight_atoms: list[int] | None = None,
    highlight_bonds: list[int] | None = None,
) -> str:
    rdmol_2d = Chem.Mol(rdmol)

    if redraw or rdmol_2d.GetNumConformers() == 0:
        rdDepictor.SetPreferCoordGen(coordgen)
        rdmol_2d = Chem.RemoveHs(rdmol_2d)
        rdDepictor.Compute2DCoords(rdmol_2d)

    rdDepictor.StraightenDepiction(rdmol_2d)

    if (highlight_bonds is None) and (highlight_atoms is not None):
        # highlight bonds between the highlighted atoms
        highlight_bonds = get_highlight_bonds(rdmol_2d, highlight_atoms)

    draw_options = moldrawer.drawOptions()

    draw_options.addAtomIndices = atom_index
    # draw_options.setHighlightColour((0,.9,.9,.8)) # Cyan highlight
    # draw_options.addBondIndices = True
    # draw_options.noAtomLabels = True
    draw_options.atomLabelDeuteriumTritium = True  # D, T
    # draw_options.explicitMethyl = True
    draw_options.singleColourWedgeBonds = True
    draw_options.addStereoAnnotation = True
    # draw_options.fillHighlights = False
    # draw_options.highlightRadius = .4
    # draw_options.highlightBondWidthMultiplier = 12
    # draw_options.variableAtomRadius = 0.2
    # draw_options.variableBondWidthMultiplier = 40
    # draw_options.setVariableAttachmentColour((.5,.5,1))
    # draw_options.baseFontSize = 1.0 # default is 0.6
    # draw_options.annotationFontScale = 1
    # draw_options.rotate = 30 # rotation angle in degrees
    # draw_options.padding = 0.2 # default is 0.05

    # for atom in rdmol_2d.GetAtoms():
    #     for key in atom.GetPropsAsDict():
    #         atom.ClearProp(key)
    # if index: # index hides polar hydrogens
    #     for atom in rdmol_2d.GetAtoms():
    #        atom.SetProp("atomLabel", str(atom.GetIdx()))
    #     #    # atom.SetProp("atomNote", str(atom.GetIdx()))
    #     #    # atom.SetProp("molAtomMapNumber", str(atom.GetIdx()))

    moldrawer.DrawMolecule(
        rdmol_2d,
        legend=legend,
        highlightAtoms=highlight_atoms,
        highlightBonds=highlight_bonds,
    )
    moldrawer.FinishDrawing()

    return moldrawer.GetDrawingText()


def render_svg(
    rdmol: Chem.Mol,
    width: int = 300,
    height: int = 300,
    legend: str = "",
    atom_index: bool = False,
    highlight_atoms: list[int] | None = None,
    highlight_bonds: list[int] | None = None,
    redraw: bool = False,
    coordgen: bool = False,
    optimize: bool = True,
) -> str:
    """Draw 2D molecule in SVG format.

    Examples:
        For Jupyternotebook, wrap the output with SVG:

        >>> from IPython.display import SVG
        >>> SVG(libr[0].to_svg())

    Args:
        rdmol (Chem.Mol): rdkit Chem.Mol object.
        width (int, optional): width. Defaults to 300.
        height (int, optional): height. Defaults to 300.
        legend (str, optional): legend. Defaults to ''.
        atom_index (bool, optional): whether to show atom index. Defaults to False.
        highlight_atoms (list[int] | None, optional): atom(s) to highlight. Defaults to None.
        highlight_bonds (list[int] | None, optional): bond(s) to highlight. Defaults to None.
        redraw (bool, optional): whether to redraw. Defaults to False.
        coordgen (bool, optional): whether to use coordgen. Defaults to False.
        optimize (bool, optional): whether to optimize SVG string. Defaults to True.

    Returns:
        str: SVG string
    """

    svg_string = render_2D_mol(
        rdmol,
        moldrawer=rdMolDraw2D.MolDraw2DSVG(width, height),
        redraw=redraw,
        coordgen=coordgen,
        legend=legend,
        atom_index=atom_index,
        highlight_atoms=highlight_atoms,
        highlight_bonds=highlight_bonds,
    )

    if optimize:
        scour_options = {
            "strip_comments": True,
            "strip_ids": True,
            "shorten_ids": True,
            "compact_paths": True,
            "indent_type": "none",
        }
        svg_string = scourString(svg_string, options=scour_options)

    return svg_string


def render_png(
    rdmol: Chem.Mol,
    width: int = 300,
    height: int = 300,
    legend: str = "",
    atom_index: bool = False,
    highlight_atoms: list[int] | None = None,
    highlight_bonds: list[int] | None = None,
    redraw: bool = False,
    coordgen: bool = False,
    trim: bool = True,
) -> Image.Image:
    """Draw 2D molecule in PNG format.

    Args:
        rdmol (Chem.Mol): rdkit Chem.Mol object.
        width (int, optional): width. Defaults to 300.
        height (int, optional): height. Defaults to 300.
        legend (str, optional): legend. Defaults to ''.
        atom_index (bool, optional): whether to show atom index. Defaults to False.
        highlight_atoms (list[int] | None, optional): atom(s) to highlight. Defaults to None.
        highlight_bonds (list[int] | None, optional): bond(s) to highlight. Defaults to None.
        redraw (bool, optional): whether to redraw. Defaults to False.
        coordgen (bool, optional): whether to use coordgen. Defaults to False.

    Returns:
        Image.Image: output PIL Image object.
    """

    png_string = render_2D_mol(
        rdmol,
        moldrawer=rdMolDraw2D.MolDraw2DCairo(width, height),
        redraw=redraw,
        coordgen=coordgen,
        legend=legend,
        atom_index=atom_index,
        highlight_atoms=highlight_atoms,
        highlight_bonds=highlight_bonds,
    )

    img = Image.open(BytesIO(png_string))

    if trim:
        img = trim_png(img)

    return img


def render_matrix_grid(
    rdmol: list[Chem.Mol],
    legend: list[str] | None,
    highlight_atoms: list[list[int]] | None = None,
    highlight_bonds: list[list[int]] | None = None,
    mols_per_row: int = 5,
    width: int = 200,
    height: int = 200,
    atom_index: bool = False,
    redraw: bool = False,
    coordgen: bool = False,
    svg: bool = True,
) -> str | Image.Image:
    """Rendering a grid image from a list of molecules.

    Args:
        rdmol (list[Chem.Mol]): list of rdkit Chem.Mol objects.
        legend (list[str]): list of legends
        highlight_atoms (list[list[int]] | None, optional): list of atom(s) to highlight. Defaults to None.
        highlight_bonds (list[list[int]] | None, optional): list of bond(s) to highlight. Defaults to None.
        mols_per_row (int, optional): molecules per row. Defaults to 5.
        width (int, optional): width. Defaults to 200.
        height (int, optional): height. Defaults to 200.
        atom_index (bool, optional): whether to show atom index. Defaults to False.
        redraw (bool, optional): whether to redraw 2D. Defaults to False.
        coordgen (bool, optional): whether to use coordgen to depict. Defaults to False.

    Returns:
        str | Image.Image: SVG string or PIL Image object.

    Reference:
        https://greglandrum.github.io/rdkit-blog/posts/2023-10-25-molsmatrixtogridimage.html
    """

    n = len(rdmol)

    if isinstance(legend, list):
        assert len(legend) == n, "number of legends and molecules must be the same"
    elif legend is None:
        legend = [
            "",
        ] * n

    if isinstance(highlight_atoms, list):
        assert len(highlight_atoms) == n, (
            "number of highlights and molecules must be the same"
        )
    elif highlight_atoms is None:
        highlight_atoms = [
            (),
        ] * n

    if isinstance(highlight_bonds, list):
        assert len(highlight_bonds) == n, (
            "number of highlights and molecules must be the same"
        )
    elif highlight_bonds is None:
        highlight_bonds = [
            (),
        ] * n

    rdmol_matrix = []
    legend_matrix = []
    highlight_atoms_matrix = []
    highlight_bonds_matrix = []

    for i in range(0, n, mols_per_row):
        rdmol_matrix.append(rdmol[i : (i + mols_per_row)])
        legend_matrix.append(legend[i : (i + mols_per_row)])
        highlight_atoms_matrix.append(highlight_atoms[i : (i + mols_per_row)])
        highlight_bonds_matrix.append(highlight_bonds[i : (i + mols_per_row)])

    return MolsMatrixToGridImage(
        molsMatrix=rdmol_matrix,
        subImgSize=(width, height),
        legendsMatrix=legend_matrix,
        highlightAtomListsMatrix=highlight_atoms_matrix,
        highlightBondListsMatrix=highlight_bonds_matrix,
        useSVG=svg,
        returnPNG=False,  # whether to return PNG data (True) or a PIL object (False)
    )


def rescale(rdmol: Chem.Mol, factor: float = 1.5) -> Chem.Mol:
    """Returns a copy of `rdmol` by a `factor`.

    Args:
        rdmol (Chem.Mol): input molecule.
        factor (float): scaling factor.

    Returns:
        Chem.Mol: a copy of rescaled rdkit.Chem.Mol object.
    """
    transformed_rdmol = Chem.Mol(rdmol)
    center = AllChem.ComputeCentroid(transformed_rdmol.GetConformer())
    tf = np.identity(4, np.float)
    tf[0][3] -= center[0]
    tf[1][3] -= center[1]
    tf[0][0] = tf[1][1] = tf[2][2] = factor
    AllChem.TransformMol(transformed_rdmol, tf)
    return transformed_rdmol


def rotation_matrix(axis: str, degree: float) -> np.ndarray:
    """Returns a numpy rotation matrix of shape (4,4).

    Args:
        axis (str): 'x' or 'y' or 'z'.
        degree (float): degree of rotation.

    Returns:
        np.ndarray: a numpy array of shape (4,4).
    """
    rad = (np.pi / 180.0) * degree
    c = np.cos(rad)
    s = np.sin(rad)
    if axis.lower() == "x":
        return np.array(
            [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, c, -s, 0.0],
                [0.0, s, c, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ]
        )
    elif axis.lower() == "y":
        return np.array(
            [
                [c, 0.0, s, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [-s, 0.0, c, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ]
        )
    elif axis.lower() == "z":
        return np.array(
            [
                [c, -s, 0.0, 0.0],
                [s, c, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ]
        )


def rotate(rdmol: Chem.Mol, axis: str, degree: float) -> None:
    """Rotate `rdmol` around given axis and degree.

    Input `rdmol` will be modified.

    Args:
        rdmol (Chem.Mol): input molecule.
        axis (str): axis of rotation, 'x' or 'y' or 'z'.
        degree (float): degree of rotation.
    """
    try:
        conf = rdmol.GetConformer()
    except:
        AllChem.Compute2DCoords(rdmol)
        conf = rdmol.GetConformer()
    R = rotation_matrix(axis, degree)
    rdMolTransforms.TransformConformer(conf, R)


class DescriptiveDraw:
    """Descriptive 2D Drawing"""

    _angles = np.linspace(0, np.pi * 2, 60)
    _circle_x, _circle_y = np.sin(_angles), np.cos(_angles)
    circle = np.vstack([_circle_x, _circle_y]).T
    style = {
        "aromatic": {
            "r": 0.3,
            "rgba": (136, 180, 168, 0.6),
            "linewidth": 1,
            "fill": True,
        },
        "conjugated": {
            "r": 0.1,
            "rgba": (51, 51, 51, 0.7),
            "linewidth": 1,
            "fill": True,
        },
        "HBA": {"r": 0.4, "rgba": (11, 57, 235, 0.7), "linewidth": 3, "fill": False},
        "HBD": {"r": 0.5, "rgba": (254, 97, 0, 0.7), "linewidth": 3, "fill": False},
        "ionizable": {
            "r": 0.5,
            "rgba": (254, 97, 0, 0.7),
            "linewidth": 3,
            "fill": False,
        },
        # Bootstrap colors
        "primary": {
            "r": 0.5,
            "rgba": (13, 110, 253, 0.7),
            "linewidth": 3,
            "fill": False,
        },
        "secondary": {
            "r": 0.5,
            "rgba": (108, 117, 125, 0.7),
            "linewidth": 3,
            "fill": False,
        },
        "success": {
            "r": 0.5,
            "rgba": (25, 135, 84, 0.7),
            "linewidth": 3,
            "fill": False,
        },
        "info": {"r": 0.5, "rgba": (13, 202, 240, 0.7), "linewidth": 3, "fill": False},
        "warning": {
            "r": 0.5,
            "rgba": (255, 193, 7, 0.7),
            "linewidth": 3,
            "fill": False,
        },
        "danger": {"r": 0.5, "rgba": (220, 53, 69, 0.7), "linewidth": 3, "fill": False},
        "light": {
            "r": 0.5,
            "rgba": (248, 249, 250, 0.7),
            "linewidth": 3,
            "fill": False,
        },
        "dark": {"r": 0.5, "rgba": (33, 37, 41, 0.7), "linewidth": 3, "fill": False},
        "blue": {"r": 0.5, "rgba": (13, 110, 253, 0.7), "linewidth": 3, "fill": False},
        "indigo": {
            "r": 0.5,
            "rgba": (102, 16, 242, 0.7),
            "linewidth": 3,
            "fill": False,
        },
        "purple": {
            "r": 0.5,
            "rgba": (111, 66, 193, 0.7),
            "linewidth": 3,
            "fill": False,
        },
        "pink": {"r": 0.5, "rgba": (214, 51, 132, 0.7), "linewidth": 3, "fill": False},
        "red": {"r": 0.5, "rgba": (220, 53, 69, 0.7), "linewidth": 3, "fill": False},
        "orange": {
            "r": 0.5,
            "rgba": (253, 126, 20, 0.7),
            "linewidth": 3,
            "fill": False,
        },
        "yellow": {"r": 0.5, "rgba": (255, 193, 7, 0.7), "linewidth": 3, "fill": False},
        "green": {"r": 0.5, "rgba": (25, 135, 84, 0.7), "linewidth": 3, "fill": False},
        "teal": {"r": 0.5, "rgba": (32, 201, 151, 0.7), "linewidth": 3, "fill": False},
        "cyan": {"r": 0.5, "rgba": (13, 202, 240, 0.7), "linewidth": 3, "fill": False},
        "white": {
            "r": 0.5,
            "rgba": (255, 255, 255, 0.7),
            "linewidth": 3,
            "fill": False,
        },
        "black": {"r": 0.5, "rgba": (0, 0, 0, 0.7), "linewidth": 3, "fill": False},
    }

    def __init__(self, rdmol: Chem.Mol, legend: str = "") -> None:
        self.rdmol = Chem.Mol(rdmol)  # copy of input molecule
        self.rdmolH = Chem.AddHs(rdmol)  # does not modify the input molecule object
        self._set_basic_nitrogens()
        self._set_acidic_oxygens()
        self.rdmol = Draw.PrepareMolForDrawing(self.rdmol)
        self.legend = legend
        self.conf = self.rdmol.GetConformer(0)
        self.canvas = None

    def _set_basic_nitrogens(self) -> None:
        nitrogens = [a for a in self.rdmol.GetAtoms() if a.GetSymbol() == "N"]
        for atom in nitrogens:
            if atom.GetIsAromatic():
                continue
            bonds = atom.GetBonds()
            conj = any([b.GetIsConjugated() for b in bonds])
            if conj:
                continue
            deg = atom.GetDegree()
            if atom.GetExplicitValence() == deg:
                atom.SetNumExplicitHs(4 - deg)
                atom.SetFormalCharge(+1)

    def _set_acidic_oxygens(self) -> None:
        # carboxylates
        oxygens = [
            i[0]
            for i in self.rdmol.GetSubstructMatches(
                Chem.MolFromSmarts("[$([OD1][CX3](=[OD1]))]")
            )
        ]
        for oidx in oxygens:
            atom = self.rdmol.GetAtomWithIdx(oidx)
            # atom.SetNumExplicitHs(0)
            atom.SetFormalCharge(-1)
            atom.UpdatePropertyCache()
        Chem.SanitizeMol(self.rdmol)

    def _get_lone_pairs(self, atom_idx: int) -> int:
        """Get number of lone pairs.

        Credit: AstraZeneca/Jazzy

        Args:
            atom_idx (int): atom index.

        Returns:
            int, number of lone pairs.
        """
        pt = Chem.GetPeriodicTable()
        atom = self.rdmolH.GetAtomWithIdx(atom_idx)
        symbol = atom.GetSymbol()
        valence_electrons = PeriodicTable.GetNOuterElecs(pt, symbol)
        unavailable_electrons = atom.GetValence(Chem.ValenceType.EXPLICIT)
        charge = atom.GetFormalCharge()
        free_electrons = valence_electrons - unavailable_electrons - charge
        return int(free_electrons / 2)

    def _get_coords(self, atom_idx: int) -> np.ndarray:
        """Get atomic coordinates

        Args:
            atom_idx (int): atom index

        Returns:
            np.ndarray: 2D coordinates
        """
        atom_pos = self.conf.GetAtomPosition(atom_idx)
        atom_pos = np.array([atom_pos.x, atom_pos.y])
        return atom_pos

    def _draw_circle(self, pos: np.ndarray, style: str) -> None:
        """Draw a circle at give position and style.

        Args:
            pos (np.ndarray): position
            style (str): drawing style
        """
        _ = DescriptiveDraw.style.get(style)
        circle_ = DescriptiveDraw.circle * _.get("r") + pos
        circle_2d = [Point2D(*c) for c in circle_]
        color = tuple([v / 256 for v in _.get("rgba")[:3]] + [_.get("rgba")[-1]])
        self.canvas.SetFillPolys(_.get("fill"))
        self.canvas.SetColour(color)
        self.canvas.SetLineWidth(_.get("linewidth"))
        self.canvas.DrawPolygon(circle_2d)

    def set_style(
        self,
        name: str,
        rgba: tuple[float, float, float, float],
        r: float = 0.52,
        linewidth: int = 1,
        fill: bool = False,
    ) -> None:
        """Set style.

        Args:
            name (str): name of style
            rgba (tuple[float,float,float,float]): RGB(0-255) and opacity (0-1)
            r (float, optional): radius of circle. Defaults to 0.52.
            linewidth (int, optional): linewidth. Defaults to 1.
            fill (bool, optional): whether to fill the circle. Defaults to False.
        """
        self.style[name] = {"r": r, "rgba": rgba, "linewidth": linewidth, "fill": fill}

    def show_styles(self) -> None:
        print(f"{'Name':<16} {'r':<8} {'rgba':<24} {'linewidth':<10} {'fill':<10}")
        for k, v in sorted(self.style.items()):
            print(
                f"{k:<16} {v['r']:<8.2f} {str(v['rgba']):<24} {v['linewidth']:<10} {v['fill']:<10}"
            )
        print()

    def draw(
        self,
        width: int = 400,
        height: int = 400,
        aromatic: bool = False,
        conjugated: bool = False,
        HBA: bool = False,
        HBD: bool = False,
        circles: Iterable | None = None,
        style: str = "primary",
        r: float | None = None,
        rgba: Iterable | None = None,
        linewidth: int | None = None,
        fill: bool | None = None,
    ) -> str:
        """Drawing SVG

        Args:
            width (int, optional): width. Defaults to 400.
            height (int, optional): height. Defaults to 400.
            aromatic (bool): whether to highlight aromatic atoms. Defaults to False.
            conjugated (bool): whether to highlight conjugated bonds. Defaults to False.
            HBA (bool): whether to circle H-bond acceptor atoms. Defaults to False.
            HBD (bool): whether to circle H-bond donor atoms. Defaults to False.
            circles (Iterable, optional): list/tuple of atom indices to circle. Defaults to None.
            style: style for circles if circles is not None.
            r (float, optional): for circles, overriding style. radius of circle. Defaults to 0.52.
            rgba (tuple[float,float,float,float]): for circles, overriding style. RGB(0-255) and opacity (0-1)
            linewidth (int, optional): for circles, overriding style. linewidth. Defaults to 1.
            fill (bool, optional): for circles, overriding style. whether to fill the circle. Defaults to False.

        Returns:
            str: SVG drawing text.
        """
        self.canvas = rdMolDraw2D.MolDraw2DSVG(width, height)
        self.canvas.drawOptions().addAtomIndices = True
        self.canvas.DrawMolecule(self.rdmol, legend=self.legend)

        if aromatic:
            for atom in self.rdmol.GetAtoms():
                aidx = atom.GetIdx()
                if atom.GetIsAromatic():
                    pos = self._get_coords(aidx)
                    self._draw_circle(pos, "aromatic")

        if conjugated:
            for bond in self.rdmol.GetBonds():
                if bond.GetIsConjugated():
                    begin_aidx = bond.GetBeginAtomIdx()
                    end_aidx = bond.GetEndAtomIdx()
                    begin_pos = self._get_coords(begin_aidx)
                    end_pos = self._get_coords(end_aidx)
                    pos = begin_pos / 2 + end_pos / 2
                    self._draw_circle(pos, "conjugated")

        if HBA:
            _HBA = Chem.MolFromSmarts(
                "[$([O,S;H1;v2]-[!$(*=[O,N,P,S])]),$([O,S;H0;v2]),$([O,S;-]),$("
                + "[N;v3;!$(N-*=!@[O,N,P,S])]),$([nH0,o,s;+0])]"
            )
            for idx in [i[0] for i in self.rdmol.GetSubstructMatches(_HBA)]:
                pos = self._get_coords(idx)
                self._draw_circle(pos, "HBA")
        if HBD:
            _HBD = Chem.MolFromSmarts("[N&!H0&v3,N&!H0&+1&v4,O&H1&+0,S&H1&+0,n&H1&+0]")
            for idx in [i[0] for i in self.rdmol.GetSubstructMatches(_HBD)]:
                pos = self._get_coords(idx)
                self._draw_circle(pos, "HBD")

        if (isinstance(circles, list) or isinstance(circles, tuple)) and isinstance(
            circles[0], int
        ):
            adhoc = self.style[style]
            if isinstance(r, float):
                adhoc.update({"r": r})
            if isinstance(linewidth, int):
                adhoc.update({"linewidth": linewidth})
            if isinstance(fill, bool):
                adhoc.update({"fill": fill})
            if isinstance(rgba, list) or isinstance(rgba, tuple):
                adhoc.update({"rgba": rgba})
            self.style["__adhoc__"] = adhoc
            for idx in circles:
                pos = self._get_coords(idx)
                self._draw_circle(pos, "__adhoc__")
            # remove the temporary style
            del self.style["__adhoc__"]

        self.canvas.FinishDrawing()

        return self.canvas.GetDrawingText()
