
from astropy.io import ascii
from astropy.coordinates import Distance
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.offsetbox as offsetbox
# from matplotlib.ticker import MultipleLocator
# from scipy import optimize
from scipy.stats import anderson_ksamp, combine_pvalues  # gaussian_kde
# from scipy.optimize import differential_evolution as DE
from scipy.special import exp1
from emcee3rc2 import ensemble


names_dict = {
    'loden565': ('LODEN565', 13.247, 0.251),
    'bh85': ('vdBH85', 13.317, 0.12085),
    'bh73': ('vdBH73', 13.498, 0.26366),
    'bh92': ('vdBH92', 12.066, 0.092136),
    'ngc4230': ('NGC4230', 13.167, 0.58768),
    'rup85': ('RUP85', 13.405, 0.11791),
    'bh106': ('vdBH106', 13.437, 0.36267),
    'trumpler13': ('TR13', 13.954, 0.17795),
    'rup88': ('RUP88', 13.704, 0.52557),
    'rup87': ('RUP87', 12.961, 0.26),
    'ngc4349': ('NGC4349', 11.375, 0.11),
    'rup162': ('RUP162', 13.23, 0.10038),
    'bh91': ('vdBH91', 11.03, 0.17141),
    'trumpler12': ('TR12', 12.721, 0.08997),
    'lynga15': ('LYNGA15', 11.741, 0.15512),
    'bh87': ('vdBH87', 11.588, 0.098)
}

plx_dict = {
    'loden565':   (3.250, 3.500, 3.020),
    'bh85':       (8.230, 8.660, 7.800),
    'bh73':       (5.480, 5.930, 5.040),
    'bh92':       (2.610, 2.720, 2.500),
    'ngc4230':    (2.970, 3.380, 2.590),
    'rup85':      (5.390, 5.620, 5.160),
    'bh106':      (5.410, 5.800, 5.030),
    'trumpler13': (5.250, 5.420, 5.100),
    'rup88':      (5.720, 6.210, 5.170),
    'rup87':      (6.190, 6.970, 5.470),
    'ngc4349':    (2.040, 2.060, 2.010),
    'rup162':     (4.970, 5.180, 4.790),
    'bh91':       (3.160, 3.330, 2.990),
    'trumpler12': (4.080, 4.220, 3.940),
    'lynga15':    (3.680, 3.900, 3.440),
    'bh87':       (2.420, 2.490, 2.350)
}

MPmin = 0.
offset = None # 'shuangjing'
nwalkers = 10
nruns = 1000


def main(MPmin, offset, nwalkers, nruns):
    """
    """
    print("\n\n{}\n\n".format(MPmin))

    for cl, clust_data in names_dict.items():

        clust_name, dm_asteca, e_dm = clust_data
        print(clust_name)

        # Read MP data
        mp_data = ascii.read('input/' + cl + '_match_memb.dat')

        # Read matched data.
        plx_data_full = ascii.read('input/' + cl + '_match.dat')

        print("Offset:", offset)
        if offset == 'lindegren':
            # Add Lindegren offset to parallax
            plx_data_full['Plx'] = plx_data_full['Plx'] + 0.029
        elif offset == 'schonrich':
            # Add  Schönrich offset to parallax
            plx_data_full['Plx'] = plx_data_full['Plx'] + 0.054
        elif offset == 'shuangjing':
            # Add Shuangjing offset to parallax
            plx_data_full['Plx'] = plx_data_full['Plx'] + 0.075

        # Separate stars in/out the cluster region.
        msk_in = np.array([
            True if _ in mp_data['ID'] else False for _ in
            plx_data_full['ID']])

        # AD test for proper motion and parallax using all the data.
        AD_data_pm = ADtest_pm(msk_in, plx_data_full)
        AD_data = ADtest_plx(msk_in, plx_data_full)

        print("AD: {:.3f}, {:.3f}, {:.3f}".format(
            AD_data[2], AD_data_pm[0][2], AD_data_pm[1][2]))
        comb_p = combine_pvalues(
            np.array([AD_data[2], AD_data_pm[0][2], AD_data_pm[1][2]]))
        print("Combined p-value: {:.3f}".format(comb_p[1]))

        # Use *ONLY* stars used in the fit process in what follows.
        msk = (mp_data['sel'] == 1) & (mp_data['MP'] >= MPmin)
        mp_data = mp_data[msk]
        # Separate stars in/out the cluster region.
        msk_in = np.array([
            True if _ in mp_data['ID'] else False for _ in
            plx_data_full['ID']])

        plx_data_in = plx_data_full[msk_in]
        plx_data_out = plx_data_full[~msk_in]
        plx_out, e_plx_out = plx_data_out['Plx'], plx_data_out['e_Plx']

        # Keep matched stars present in the 'plx_data' array.
        msk = np.array([
            True if _ in plx_data_in['ID'] else False for _ in
            mp_data['ID']])
        print("Stars with no match: {}".format(len(mp_data) - sum(msk)))
        mp_data = mp_data[msk]

        # Sorting is important!
        plx_data_in.sort('ID')
        mp_data.sort('ID')

        # # Parallax data.
        # print("Preparing {} Plx data".format(clust_name))
        # plx_bay, ph_plx, pl_plx, burn, chains = plxPlot(
        #     clust_name, plx_data_in['Plx'], plx_data_in['e_Plx'],
        #     mp_data['MP'], nwalkers=nwalkers, nruns=nruns)

        plx_bay, ph_plx, pl_plx = plx_dict[cl]

        # Make final plot
        fig = plt.figure(figsize=(30, 25))
        gs = gridspec.GridSpec(10, 12)
        print("Plotting")
        finalPLot(
            fig, gs, clust_name, AD_data_pm, AD_data, plx_data_in['Gmag'],
            mp_data['MP'], plx_data_in['Plx'], plx_data_in['e_Plx'],
            plx_bay, ph_plx, pl_plx, plx_out, e_plx_out, dm_asteca, e_dm)
        fig.tight_layout()
        nameout = 'output/plx_' + str(MPmin) + '_' + clust_name + '.png'
        plt.savefig(nameout, dpi=300, bbox_inches='tight')

        # plt.style.use('seaborn-darkgrid')
        # fig = plt.figure(figsize=(30, 25))
        # gs = gridspec.GridSpec(4, 1)
        # ax = plt.subplot(gs[0])
        # ax.minorticks_on()
        # plt.plot(burn.T[0], c='grey', alpha=.5)
        # Nb, Nc = burn.T[0].shape[0], chains.T[0].shape[0]
        # plt.plot(range(Nb, Nb + Nc), chains.T[0], alpha=.5)
        # fig.tight_layout()
        # nameout = 'output/chain_' + str(MPmin) + '_' + clust_name + '.png'
        # plt.savefig(nameout, dpi=300, bbox_inches='tight')

        plt.clf()
        plt.close("all")

        print("Done\n")

    print("End")


def ADtest_pm(msk_in, plx_data_full):
    pmRA_in, pmDEC_in = plx_data_full['pmRA'][msk_in],\
        plx_data_full['pmDE'][msk_in]
    pmRA_out, pmDEC_out = plx_data_full['pmRA'][~msk_in],\
        plx_data_full['pmDE'][~msk_in]

    return [list(anderson_ksamp([pmRA_in, pmRA_out])),
            list(anderson_ksamp([pmDEC_in, pmDEC_out]))]


def ADtest_plx(msk_in, plx_data_full):
    plx_in, e_plx_in = plx_data_full[msk_in]['Plx'],\
        plx_data_full[msk_in]['e_Plx']
    plx_out, e_plx_out = plx_data_full[~msk_in]['Plx'],\
        plx_data_full[~msk_in]['e_Plx']

    # Run the AD test using *all* stars with parallax data.
    AD_ks, cv_ka, pv_ks = anderson_ksamp([plx_in, plx_out])

    x_cl_kde, y_cl_kde = kde_1d(plx_in, e_plx_in)
    x_fl_kde, y_fl_kde = kde_1d(plx_out, e_plx_out)

    plx_med, plx_std = np.median(plx_out), np.std(plx_out)
    x_fl_kde_max, x_fl_kde_min = plx_med - 2. * plx_std, plx_med + 3. * plx_std

    return [AD_ks, cv_ka, pv_ks, x_cl_kde, y_cl_kde, x_fl_kde, y_fl_kde,
            x_fl_kde_max, x_fl_kde_min]


def plxPlot(clust_name, plx, e_plx, mp, nwalkers, nruns):
    """
    Parameters for the parallax plot.
    """

    # # Turn off the MPs
    # mp = 1.
    print("N stars in Plx analysis: {}".format(len(plx)))

    def lnlike(mu, x, B2):
        """
        Model defined in Bailer-Jones (2015), Eq (20), The shape parameter s_c
        is marginalized.
        """
        lim_u = 5.

        def distFunc(r_i):
            sc_int = .5 * exp1(.5 * ((r_i - mu) / lim_u)**2)
            sc_int.T[np.isinf(sc_int.T)] = 0.
            return B2 * sc_int

        # Double integral
        int_exp = np.trapz(distFunc(x), x, axis=0)

        return np.sum(np.log(mp * int_exp))

    def lnprior(w_t):  # , w_p, s_p):
        """
        Prior
        """
        if w_t < 0.:
            return -np.inf
        # # Log prior, Gaussian > 0.
        # return -0.5 * ((w_p - w_t) / s_p)**2
        # Uniform prior
        return 0.

    def lnprob(w_t, x, B2):  # , w_p, s_p):
        lp = lnprior(w_t)  # , w_p, s_p)
        if np.isinf(lp):
            return -np.inf
        return lp + lnlike(w_t, x, B2)

    # # Define the 'r_i' values used to evaluate the integral.
    # int_max = 20.
    # N = int(int_max / 0.01)
    # x = np.linspace(.1, int_max, N).reshape(-1, 1)
    # B1 = ((plx - (1. / x)) / e_plx)**2
    # B2 = (np.exp(-.5 * B1) / e_plx)

    # # Use DE to estimate the ML
    # def DEdist(model):
    #     return -lnlike(model, x, B2)
    # bounds = [[0., 20.]]
    # result = DE(DEdist, bounds, popsize=20, maxiter=50)
    # print(result.x)

    # Prior parameters.
    # # This is the mean for the Gaussian prior.
    # w_p = result.x
    # # This is the STTDEV of the Gaussian prior.
    # s_p = 1.

    # Define the 'r_i' values used to evaluate the integral.
    int_max = 20.  # w_p + 5.
    N = int(int_max / 0.01)
    x = np.linspace(.1, int_max, N).reshape(-1, 1)
    B1 = ((plx - (1. / x)) / e_plx)**2
    B2 = (np.exp(-.5 * B1) / e_plx)

    ndim = 1
    sampler = ensemble.EnsembleSampler(
        nwalkers, ndim, lnprob, args=(x, B2))  # , w_p, s_p
    # Initial guesses.
    # pos0 = [w_p + .5 * np.random.normal() for i in range(nwalkers)]

    # Set 'nwalkers' initial positions distributed in the [0, 10] kpc range.
    pos = [np.array([_]) for _ in np.linspace(0., 10., nwalkers).tolist()]
    # sampler.run_mcmc(pos, nruns)
    print(" Iteration ({}), autocorr time".format(nruns))
    for i, _ in enumerate(sampler.sample(pos, iterations=nruns)):
        if i % 100:
            continue
        actime = sampler.get_autocorr_time(tol=0)[0]
        Neff = (nwalkers * i) / actime
        print(i, actime, Neff)
        if Neff > 1000:
            break

    # Remove burn-in
    nburn = int(i / 4.)
    samples = sampler.chain[:, nburn:, :].reshape((-1, ndim))

    # Median estimator of samples.
    # 16th, 84th percentiles
    pl_plx, plx_bay, ph_plx = np.percentile(samples, [16, 50, 84])
    print("Plx Bys '{}': ({:.3f}, {:.3f}, {:.3f}),".format(
        clust_name, pl_plx, plx_bay, ph_plx))

    m_accpt_fr = np.mean(sampler.acceptance_fraction)
    print("Mean acceptance fraction: {:.3f}".format(m_accpt_fr))
    print("Autocorrelation time: {:.2f}".format(
        sampler.get_autocorr_time(tol=0)[0]))

    return plx_bay, ph_plx, pl_plx, sampler.chain[:, :nburn, :],\
        sampler.chain[:, nburn:, :]


def finalPLot(
    fig, gs, reg_name, AD_data_pm, AD_data, mmag_plx, mp_plx, plx,
        e_plx, plx_bay, ph_plx, pl_plx, plx_out, e_plx_out, dm_asteca, e_dm):
    '''
    Parallax versus magnitude, parallax KDEs, and final results.
    '''

    # x_max_cmd, x_min_cmd, y_min_cmd, y_max_cmd = diag_limits(
    #     'mag', col_plx, mmag_plx)

    # plt.style.use('seaborn-darkgrid')

    ax = plt.subplot(gs[0:2, 0:2])
    ax.set_title("{}".format(reg_name), fontsize=12, x=.13, y=.94)
    plt.xlabel('Plx [mas]', fontsize=12)
    plt.ylabel('G', fontsize=12)
    # Set minor ticks
    ax.minorticks_on()
    # ax.axvspan(-100., 0., alpha=0.25, color='grey', zorder=1)

    # Weighted average and its error.
    # Source: https://physics.stackexchange.com/a/329412/8514
    plx_w = 1. / e_plx
    # e_plx_w = np.sqrt(np.sum(np.square(e_plx * plx_w))) / np.sum(plx_w)
    plx_wa = np.average(plx, weights=plx_w)

    cm = plt.cm.get_cmap('RdYlBu_r')  # viridis
    # Plot stars selected to be used in the best fit process.
    plt.scatter(
        plx, mmag_plx, marker='o', c=mp_plx, s=30, edgecolors='black',
        cmap=cm, lw=0.35, zorder=4, label=None)
    ax.errorbar(
        plx, mmag_plx, xerr=e_plx, fmt='none', elinewidth=.35,
        ecolor='grey', label=None)

    # Bayesian
    # d_pc = Distance((1000. * round(plx_bay, 2)), unit='pc')
    # dl_pc = Distance((1000. * round(pl_plx, 2)), unit='pc')
    # dh_pc = Distance((1000. * round(ph_plx, 2)), unit='pc')
    d_pc = Distance(1000. * plx_bay, unit='pc')
    dl_pc = Distance(1000. * pl_plx, unit='pc')
    dh_pc = Distance(1000. * ph_plx, unit='pc')
    plt.axvline(
        x=1. / plx_bay, linestyle='--', color='b', lw=1.2, zorder=5,
        label=r"$Plx_{{Bayes}}$")

    plx_asteca = 1000. / 10 ** ((dm_asteca + 5.) / 5.)
    pc50_asteca = round(1. / plx_asteca, 2)
    e_pc_asteca = round(.2 * np.log(10.) * pc50_asteca * e_dm, 2)
    pc16_asteca = pc50_asteca - e_pc_asteca
    pc84_asteca = pc50_asteca + e_pc_asteca
    pc50_asteca, pc16_asteca, pc84_asteca = 1000. * pc50_asteca,\
        1000. * pc16_asteca, 1000. * pc84_asteca
    plt.axvline(
        x=plx_asteca, linestyle=':', color='g', lw=1.5, zorder=5,
        label=r"$Plx_{{AsteCA}}$")

    # Weighted average
    plt.axvline(
        x=plx_wa, linestyle='--', color='r', lw=.85, zorder=5,
        label=r"$Plx_{{wa}}$")
    # Median
    plx_gr_zero = plx[plx > 0.]
    plt.axvline(
        x=np.median(plx_gr_zero), linestyle='--', color='k', lw=.85, zorder=5,
        label=r"$Plx_{{>0|med}}$")

    ax.legend(fontsize=12, loc=4)

    cbar = plt.colorbar(pad=.01, fraction=.02, aspect=50)
    cbar.ax.tick_params(labelsize=10)
    # cbar.set_label('MP', size=8)

    min_plx, max_plx = np.median(plx) - 2. * np.std(plx),\
        np.median(plx) + 2.5 * np.std(plx)
    plt.xlim(min_plx, max_plx)
    # ax.set_ylim(ax.get_ylim()[::-1])
    plt.gca().invert_yaxis()

    #
    AD_plx, cv_ka, pv_plx, x_cl_kde, y_cl_kde, x_fl_kde, y_fl_kde,\
        x_fl_kde_max, x_fl_kde_min = AD_data
    ax = plt.subplot(gs[0:2, 2:4])
    ax.minorticks_on()
    # ax.axvspan(-100., 0., alpha=0.25, color='grey', zorder=1)
    plt.xlabel('Plx [mas]', fontsize=12)
    plt.plot(x_fl_kde, y_fl_kde / max(y_fl_kde), color='k', lw=1., ls='--',
             zorder=4, label="Field region")
    plt.plot(x_cl_kde, y_cl_kde / max(y_cl_kde), color='r', lw=1.5, zorder=6,
             label="Cluster region")
    plt.axvline(x=1. / plx_bay, linestyle='--', color='b', lw=1.2, zorder=5,
                label=r"$Plx_{Bayes}$")
    plt.axvline(
        x=plx_asteca, linestyle=':', color='g', lw=1.5, zorder=5,
        label=r"$Plx_{ASteCA}$")
    ax.legend(fontsize=12, loc=0)
    plt.xlim(x_fl_kde_max, x_fl_kde_min)
    plt.ylim(-.01, 1.05)

    # Add text box to the right of the synthetic cluster.
    ax_t = plt.subplot(gs[0:2, 4:6])
    ax_t.axis('off')  # Remove axis from frame.
    t0 = r"$d_{{Bayes}}={:.0f}_{{{:.0f}}}^{{{:.0f}}}\;[pc]$".format(
        d_pc.value, dl_pc.value, dh_pc.value)
    t1 = r"$(Plx_{{Bayes}}={:.3f},\;\mu_{{0}}={:.2f})$".format(
        1. / plx_bay, d_pc.distmod.value)
    t2 = r"$d_{{ASteCA}}={:.0f}_{{{:.0f}}}^{{{:.0f}}}\;[pc]$".format(
        pc50_asteca, pc16_asteca, pc84_asteca)
    t3 = r"$(Plx_{{ASteCA}}={:.3f},\;\mu_{{0}}={:.2f})$".format(
        plx_asteca, dm_asteca)
    t4 = r"$Plx_{{wa}} = {:.3f}$".format(plx_wa)
    t5 = r"$Plx_{{>0|med}} = {:.3f}$".format(np.median(plx_gr_zero))

    AD_ra, _, pv_ra = AD_data_pm[0]
    AD_dec, _, pv_dec = AD_data_pm[1]
    comb_p = combine_pvalues(np.array([pv_plx, pv_ra, pv_dec]))
    t6 = (r"$AD_{{Plx}}={:.3f},\;pvalue={:.3f}$").format(AD_plx, pv_plx)
    t7 = (r"$AD_{{PM(\alpha)}}={:.3f},\;pvalue={:.3f}$").format(AD_ra, pv_ra)
    t8 = (r"$AD_{{PM(\delta)}}={:.3f},\;pvalue={:.3f}$").format(AD_dec, pv_dec)
    # t9 = (r"$(cv_{{0.05}}={:.3f})$").format(cv_ka[2])
    t9 = "Combined " + r"$pvalue={:.3f}$".format(comb_p[1])

    text = t0 + '\n\n' + t1 + '\n\n' + t2 + '\n\n' + t3 + '\n\n' + t4 +\
        ' ; ' + t5 + '\n\n\n' + t6 + '\n\n' + t7 + '\n\n' + t8 + '\n\n' + t9
    ob = offsetbox.AnchoredText(
        text, pad=1, loc=6, borderpad=-2, prop=dict(size=13))
    ob.patch.set(alpha=0.85)
    ax_t.add_artist(ob)


def kde_1d(xarr, xsigma, grid_dens=500):
    '''
    Take an array of x data with their errors, create a grid of points in x
    and return the 1D KDE density map.
    '''

    # Grid density (number of points).
    gd_c = complex(0, grid_dens)

    # Define grid of points in x where the KDE will be evaluated.
    xmean, xstd = np.nanmedian(xarr), np.nanstd(xarr)
    xmax, xmin = xmean + 5. * xstd, xmean - 5. * xstd
    x = np.mgrid[xmin:xmax:gd_c]

    # # Scipy's norm factor
    # # https://github.com/scipy/scipy/blob/v1.1.0/scipy/stats/kde.py
    # d, n = 1, xarr.size
    # data_covariance = np.cov(xarr)
    # data_inv_cov = 1. / data_covariance
    # scotts_factor = np.power(n, -1. / (d + 4))
    # inv_cov = 1. # data_inv_cov / scotts_factor**2
    # covariance = data_covariance * scotts_factor**2
    # norm_factor = np.sqrt(2 * np.pi * covariance) * n
    # print(inv_cov, norm_factor)

    # xsigma = 1.

    positions = np.vstack([x.ravel()])
    # Evaluate KDE in x grid.
    vals = []
    for p in zip(*positions):
        valx = np.exp(-0.5 * ((p - xarr) / xsigma)**2) / xsigma
        vals.append(np.sum(valx))
    z = np.array(vals) / (np.sqrt(2 * np.pi) * xarr.size)

    return positions[0], z

    # # Define KDE limits.
    # kernel_cl = gaussian_kde(xarr.filled(0.))
    # # KDE for plotting.
    # kde_pl = np.reshape(kernel_cl(x).T, x.shape)

    # return x, kde_pl


def diag_limits(yaxis, phot_x, phot_y):
    '''
    Define plot limits for *all* photometric diagrams.
    '''
    # TODO deprecated
    # min_x, max_x, min_y, max_y = kde_limits(phot_x, phot_y)

    x_median, x_std = np.median(phot_x), 1.5 * np.std(phot_x)
    x_min_cmd, x_max_cmd = x_median - 3. * x_std, x_median + 4. * x_std
    y_median, y_std = np.median(phot_y), np.std(phot_y)
    min_y, max_y = y_median - y_std, y_median + y_std

    # Define diagram limits.
    y_min_cmd = max_y + 1.25
    # If photometric axis y is a magnitude, make sure the brightest star
    # is always plotted.
    if yaxis == 'mag':
        y_max_cmd = min(phot_y) - 1.
    else:
        y_max_cmd = min_y - 1.

    return x_max_cmd, x_min_cmd, y_min_cmd, y_max_cmd


if __name__ == '__main__':
    # for mpmin in (0.):
    main(MPmin, offset, nwalkers, nruns)
