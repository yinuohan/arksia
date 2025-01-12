"""This module contains a function to obtain results from fits/analysis of multiple sources
(written by Jeff Jennings)."""

import os
import json
import numpy as np 
import matplotlib.pyplot as plt 

from arksia.pipeline import model_setup
from arksia.input_output import load_bestfit_profiles

def main(gen_par_f='./pars_gen.json',
         source_par_f='./pars_source.json', 
         phys_par_f='./summary_disc_parameters.csv',
         profiles_txt=True, profiles_fig=True, robust=0.5,
         include_rave=False
         ):
    """
    Generate summary radial profile results across multiple survey sources.

    Parameters
    ----------       
    gen_par_f : string, default='pars_gen.json'
        Path to the general parameters file  
    source_par_f : string, default='pars_source.json'
        Path to the parameter file with custom values for each source         
    phys_par_f : string, default='pars_gen.json'
        Path to the physical parameters file
    profiles_txt : bool, default=True
        Whether to produce a .txt file per source containting the 
        clean, rave, frank brightness profiles (sampled at same radii)
    profiles_fig : bool, default=True
        Whether to produce a single figure showing brightness profiles for 
        all sources
    robust : float, default=2.0
        Robust weighting value to use for retrieving clean, rave results
    include_rave : bool, default=True
        Whether to include rave results in summary

    Returns
    -------
    figs : `plt.figure` instance
        The generated figures, produced if `profiles_fig` is True
    """

    # get all source names
    source_pars = json.load(open(source_par_f, 'r'))
    disk_names = []
    for dd in source_pars:
        disk_names.append(dd)

    fig0, axs0 = plt.subplots(nrows=5, ncols=4, figsize=(10, 10), squeeze=True)
    fig1, axs1 = plt.subplots(nrows=5, ncols=4, figsize=(10, 10), squeeze=True)
    figs, axs = [fig0, fig1], [axs0, axs1]

    gen_pars = json.load(open(gen_par_f, 'r'))
    source_pars = json.load(open(source_par_f, 'r'))

    for ii, jj in enumerate(disk_names):
        # update generic parameters that vary by source
        gen_pars['base']['input_dir'] = f"./{jj}"
        disk_pars = source_pars[jj]
        gen_pars['clean']['robust'] = disk_pars["clean"]["bestfit"]["robust"]

        # save updated gen_pars
        gen_pars_current = os.path.join(os.path.dirname(gen_par_f), 'pars_gen_temp.json')
        with open(gen_pars_current, 'w') as f:
            json.dump(gen_pars, f)

        # generate model for each source
        class parsed_args():
            base_parameter_filename = gen_pars_current
            source_parameter_filename = source_par_f
            physical_parameter_filename = phys_par_f
            disk = jj
        model = model_setup(parsed_args)

        # best-fit clean, rave, frank profile for each source
        fits = load_bestfit_profiles(model, robust, include_rave=include_rave)
        [[rc, Ic, Iec], [grid, Vc]] = fits[0]
        [[rf, If, Ief], [grid, Vf], sol] = fits[2]
        if include_rave:
            [[rr, Ir, Ier_lo, Ier_hi], [grid, Vr]] = fits[1]        

        # interpolate clean and rave profiles onto frank radial points 
        Ic_interp = np.interp(rf, rc, Ic)
        Iec_interp = np.interp(rf, rc, Iec)
        if include_rave:
            Ir_interp = np.interp(rf, rr, Ir)
            Ier_lo_interp = np.interp(rf, rr, Ier_lo)
            Ier_hi_interp = np.interp(rf, rr, Ier_hi)

            Is_interp = [Ic_interp, Ir_interp, If]
            Ies_interp = [[Iec_interp, Iec_interp], [Ier_lo_interp, Ier_hi_interp], [Ief, Ief]]
        else:
            Is_interp = [Ic_interp, If]
            Ies_interp = [[Iec_interp, Iec_interp], [Ief, Ief]]


        if profiles_txt:
            ff = '{}/{}_radial_profiles.txt'.format(model["base"]["save_dir"], jj)
            print('  Survey summary: saving radial profiles to {}'.format(ff))

            # save .txt file per source with clean,rave,frank profiles
            header=f"dist={model['base']['dist']} [au].\nAll brightnesses in [Jy/steradian].\nUncertainties not comparable across models. "

            if include_rave:
                profiles = np.array([rf * model["base"]["dist"], Ic_interp, Iec_interp, 
                              If, Ief, Ir_interp, Ier_lo_interp, Ier_hi_interp
                              ])
                header += "Rave uncertainties have unique lower and upper bounds.\nColumns: "
                header += "r [au]\t\tI_clean\t\tsigma_clean\t\tI_frank\t\tsigma_frank\t\tI_rave\t\tsigma_lower_rave\t\tsigma_upper_rave"
            else:
                profiles = np.array([rf * model["base"]["dist"], Ic_interp, Iec_interp,
                              If, Ief
                              ])
                header += "\nColumns: r [au]\t\tI_clean\t\tsigma_clean\t\tI_frank\t\tsigma_frank"               
            
            np.savetxt(ff, profiles.T, header=header)


        if profiles_fig:
            # generate, save figures for brightness profiles of all sources and brightness profiles with uncertainties
            for hh in range(2):
                fig = figs[hh]
                ax = axs[hh]

                # flatten axes
                ax = [bb for aa in ax for bb in aa]
                cols, labs = ['C1', 'C2'], ['clean', 'frank']
                if include_rave: 
                    cols, labs = cols.append('C3'), labs.append('rave')                    

                for kk, ll in enumerate(Is_interp):     
                    # plot profile
                    ax[ii].plot(rf * model["base"]["dist"], ll / 1e6, c=cols[kk], label=labs[kk])
                
                    if hh == 1:
                        # 1 sigma uncertainty band
                        band = ax[ii].fill_between(rf * model["base"]["dist"], 
                                            (ll - Ies_interp[kk][0]) / 1e6, (ll + Ies_interp[kk][1]) / 1e6, 
                                        color=cols[kk], alpha=0.4)
                        # prevent 1 sigma band from altering y-limits
                        band.remove()
                        ax[ii].relim()
                        ax[ii].add_collection(band, autolim=False)

                ax[ii].axhline(y=0, ls='--', c='k')

                fstar_ujy = model["frank"]["fstar"] * 1e6
                ax[ii].set_title(f"{jj}, " + r"$F_* =$ " + f"{fstar_ujy:.0f} uJy", fontsize=10)

                if ii == 0:
                    ax[ii].legend(loc='upper right', fontsize=8)
                    ax[ii].set_xlabel('r [au]')
                    ax[ii].set_ylabel(r'I [MJy sterad$^{-1}$]')

    if profiles_fig:
        print('  Survey summary: making survey summary figure')
    fig1.suptitle(r'$1\sigma$ uncertainties do not include systematic unc., and are not comparable across models')    

    ff0 = '{}/survey_profile_summary.png'.format(model["base"]["save_dir"])
    ff1 = '{}/survey_profile_summary_unc.png'.format(model["base"]["save_dir"])
    print('    saving figures to {} and {}'.format(ff0, ff1))

    plt.figure(fig0); plt.tight_layout(); plt.savefig(ff0, dpi=300)
    plt.figure(fig1); plt.tight_layout(); plt.savefig(ff1, dpi=300)

    os.remove(gen_pars_current)

    return figs
    
if __name__ == "__main__":
    main()