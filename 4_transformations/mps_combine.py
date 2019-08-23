
from os import getcwd, listdir
from os.path import join, realpath, dirname
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from mpl_toolkits.axes_grid1 import make_axes_locatable
from astropy.table import Table
import numpy as np
from scipy.spatial.distance import cdist


def main():
    """
    Read  image files, extract the proper plots, and generate a single image
    for each cluster.
    """
    names_dict = {
        'ngc4230': 'NGC4230', 'rup85': 'RUP85',
        'bh106': 'vdBH106', 'trumpler13': 'TR13',
        'rup88': 'RUP88', 'rup87': 'RUP87',
        'ngc4349': 'NGC4349', 'rup162': 'RUP162',
        'bh91': 'vdBH91', 'trumpler12': 'TR12',
        'lynga15': 'LYNGA15', 'bh87': 'vdBH87',
        'bh85': 'vdBH85', 'loden565': 'LODEN565',
        'bh92': 'vdBH92', 'bh73': 'vdBH73'}

    r_path = realpath(join(getcwd(), dirname(__file__)))

    # Crop image sections
    for fname, name in names_dict.iteritems():
        # if name == 'vdBH73':
        print(fname)
        data = []

        filename = fname + '_match_A2.png'
        im = plt.imread(join(r_path, filename))
        # im_croppped = im[50:800, :740, :]
        im_croppped = im[70:740, :730, :]
        # print(im_croppped.shape)
        # plt.imshow(im_croppped);plt.show()
        data.append(im_croppped)
        # im_croppped = im[762:, :740, :]
        im_croppped = im[820:, :730, :]
        # plt.imshow(im_croppped);plt.show()
        # print(im_croppped.shape)
        data.append(im_croppped)

        filename = fname + '_match_C.png'
        im = plt.imread(join(r_path, filename))
        im_croppped = im[50:800, 1489:, :]
        # plt.imshow(im_croppped);plt.show()
        # print(im_croppped.shape)
        data.append(im_croppped)

        filename = fname + '_match_B.png'
        im = plt.imread(join(r_path, filename))
        im_croppped = im[40:790, :4030, :]
        # plt.imshow(im_croppped);plt.show()
        # print(im_croppped.shape)
        data.append(im_croppped)

        makePlots(fname, name, data)

    print("Finished")


def transfPlot(fname, gs):
    """
    Carrasco Gaia DR2 transformations:
    https://gea.esac.esa.int/archive/documentation/GDR2/Data_processing/
    chap_cu5pho/sec_cu5pho_calibr/ssec_cu5pho_PhotTransf.html
    """

    rpath = '/home/gabriel/Github/asteca-project/ASteCA/input/sixteen_cls/'

    t = Table.read(rpath + fname + '_match.dat', format='ascii')
    Vm, eVm, BVm, eBVm, VIm, eVIm, Gm, eGm, BPRPm =\
        t['V'], t['Verr'], t['BV'], t['BVerr'], t['VI'], t['VIerr'],\
        t['Gmag'], t['e_Gmag'], t['BP-RP']
    # Apply masks
    Gmsk = Gm < 13.
    eGmsk = eGm < 0.01
    BVmsk = (-0.3 < BVm) & (BVm < 2.4)
    VImsk = (-.3 < VIm) & (VIm < 2.7)
    BPRPmsk = (-.5 < BPRPm) & (BPRPm < 2.75)
    # Filters on our photometry
    eVmsk = eVm < 0.05
    eBVmsk = eBVm < 0.05
    eVImsk = eVIm < 0.05
    msk = Gmsk & eGmsk & BVmsk & VImsk & eVmsk & eBVmsk & eVImsk & BPRPmsk
    Vm, BVm, VIm, Gm, BPRPm = Vm[msk], BVm[msk], VIm[msk],\
        Gm[msk], BPRPm[msk]

    Ninterp = 1000

    def PolyCoefficients(x, coeffs):
        """
        Returns a polynomial for ``x`` values for the ``coeffs`` provided.
        The coefficients must be in ascending order (``x**0`` to ``x**p``).
        """
        y = 0
        for p in range(len(coeffs)):
            y += coeffs[p] * x**p
        return y

    # G-V vs B-V
    x = np.linspace(min(BVm), max(BVm), Ninterp)
    coeffs = [-0.02907, -0.02385, -0.2297, -0.001768]
    y = PolyCoefficients(x, coeffs)

    # Range of applicability
    delta1 = np.median(np.min(cdist(
        np.array([BVm, Gm - Vm]).T, np.array([x, y]).T), axis=1))
    # plt.subplot(131)
    ax = plt.subplot(gs[6])
    ax.grid(which='major', axis='both', linestyle='--', color='grey', lw=.5)
    plt.title(
        r"GDR2 (G<13, $\sigma_{{G}}<0.01$) " +
        r"($\Delta_{{median}}\approx{:.4f}$)".format(delta1), fontsize=14)
    plt.xlabel(r"$B-V$", fontsize=14)
    plt.ylabel(r"$G-V$", fontsize=14)
    plt.plot(x, y, c='orange', label="Carrasco transformation", zorder=-1)
    plt.scatter(BVm, Gm - Vm, label="N={}".format(len(Vm)), c=Vm)
    plt.xlim(max(-.4, min(BVm) - .05), min(2.5, max(BVm) + .05))
    plt.legend(fontsize=12)

    # G-V vs V-I
    x = np.linspace(np.nanmin(VIm), np.nanmax(VIm), Ninterp)
    coeffs = [-0.01746, 0.008092, -0.2810, 0.03655]
    y = PolyCoefficients(x, coeffs)

    delta2 = np.median(np.min(cdist(
        np.array([VIm, Gm - Vm]).T, np.array([x, y]).T), axis=1))
    # plt.subplot(132)
    ax = plt.subplot(gs[7])
    ax.grid(which='major', axis='both', linestyle='--', color='grey', lw=.5)
    plt.title(
        r"GDR2 (G<13, $\sigma_{{G}}<0.01$) " +
        r"($\Delta_{{median}}\approx{:.4f}$)".format(delta2), fontsize=14)
    plt.xlabel(r"$V-I$", fontsize=14)
    plt.ylabel(r"$G-V$", fontsize=14)
    plt.plot(x, y, c='orange', zorder=-1)
    plt.scatter(VIm, Gm - Vm, label="N={}".format(len(Vm)), c=Vm)
    plt.xlim(max(-.4, min(VIm) - .05), min(2.8, max(VIm) + .05))

    # G-V vs G_BP-G_RP
    x = np.linspace(min(BPRPm), max(BPRPm), Ninterp)
    coeffs = [-0.01760, -0.006860, -0.1732]
    y = PolyCoefficients(x, coeffs)

    delta3 = np.median(np.min(cdist(
        np.array([BPRPm, Gm - Vm]).T, np.array([x, y]).T), axis=1))
    # ax = plt.subplot(133)
    ax = plt.subplot(gs[8])
    ax.grid(which='major', axis='both', linestyle='--', color='grey', lw=.5)
    plt.title(
        r"GDR2 (G<13, $\sigma_{{G}}<0.01$) " +
        r"($\Delta_{{median}}\approx{:.4f}$)".format(delta3), fontsize=14)
    plt.xlabel(r"$BP-RP$", fontsize=14)
    plt.ylabel(r"$G-V$", fontsize=14)
    plt.plot(x, y, c='orange', zorder=-1)
    # cm = plt.cm.get_cmap('Reds')
    sc = plt.scatter(BPRPm, Gm - Vm, label="N={}".format(len(Vm)), c=Vm)
    plt.xlim(max(-.6, min(BPRPm) - .05), min(2.8, max(BPRPm) + .05))

    # create an axes on the right side of ax. The width of cax will be 5%
    # of ax and the padding between cax and ax will be fixed at 0.05 inch.
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="2%", pad=0.02)
    cbar = plt.colorbar(sc, cax=cax)
    # cbar = plt.colorbar(sc)
    cbar.ax.tick_params(labelsize=12)
    cbar.ax.invert_yaxis()
    cbar.set_label('V [mag]', fontsize=12)

    print("{:.4f} {:.4f} {:.4f}".format(delta1, delta2, delta3))


def makePlots(fname, name, data):
    """
    """
    dpi = 150
    fig = plt.figure(figsize=(20, 20))
    gs = gridspec.GridSpec(3, 3)

    ax = plt.subplot(gs[0])
    ax.imshow(data[0])
    ax.set_xticks([])
    ax.set_yticks([])
    ax.axis('off')

    ax = plt.subplot(gs[1])
    ax.imshow(data[1])
    ax.set_xticks([])
    ax.set_yticks([])
    ax.axis('off')

    ax = plt.subplot(gs[2])
    ax.set_title("{}".format(
        "G + BVI + Plx + PMs", fontsize="10", y=1.,
        bbox=dict(facecolor='white', alpha=0.75)))
    ax.imshow(data[2])
    ax.set_xticks([])
    ax.set_yticks([])
    ax.axis('off')

    # for (r, im) in data:
    ax = plt.subplot(gs[1, :])
    ax.imshow(data[3])
    ax.set_xticks([])
    ax.set_yticks([])
    ax.axis('off')

    transfPlot(fname, gs)

    fig.tight_layout()
    fig.savefig(join('out', name + '_comb.png'), dpi=dpi, bbox_inches='tight')
    plt.close()


if __name__ == '__main__':
    main()