"""This module runs tests to confirm the code is working correctly."""

import os 
import json
import numpy as np 

from arksia import input_output, pipeline, analysis, bulk_pipeline_run, bulk_pipeline_results

tmp_dir = '/tmp/arksia/tests'
os.makedirs(tmp_dir, exist_ok=True)

def save_custom_gen_pars(gen_pars):
    """Save an altered generic parameters file"""

    gen_pars['base']['input_dir'] = 'test/mockAS209'
    gen_pars['base']['output_dir'] = tmp_dir

    gen_pars_file = os.path.join(tmp_dir, 'gen_pars.json')
    with open(gen_pars_file, 'w') as f:
        json.dump(gen_pars, f)

    return gen_pars_file


def update_frank_pars(gen_pars):
    """Update default generic parameters for tests using frank"""
    gen_pars['base']['run_frank'] = True
    gen_pars['frank']['rout'] = 1.5
    gen_pars['frank']['N'] = 50
    gen_pars['frank']['alpha'] = [1.5]
    gen_pars['frank']['wsmooth'] = [1e-1]
    gen_pars['frank']['scale_height'] = None    
    gen_pars['frank']['method'] = 'Normal'

    return gen_pars


def _run_pipeline(gen_pars_file):
    """Generic routine to invoke pipeline"""

    # Dummy source-specific parameters file
    source_pars_file = 'test/mockAS209/mock_pars_source.json'

    # Dummy physical parameters file
    phys_pars_file = 'test/mockAS209/mock_pars_phys.csv'

    # Call pipeline
    pipeline.main(['-b', gen_pars_file, '-s', source_pars_file, '-p', phys_pars_file, '-d', 'mockAS209'])


def test_concat_vis():
    """Join text files to create a .npz visibility table with expected number of parameters"""
    
    fake_vis0 = np.empty((6, 10))
    fake_vis1 = np.empty((6, 10))
    f0, f1 = tmp_dir + '/fake_vis0.txt', tmp_dir + '/fake_vis1.txt'
    np.savetxt(f0, fake_vis0.T)
    np.savetxt(f1, fake_vis1.T)

    input_output.concatenate_vis(in_path=[f0, f1], out_path=tmp_dir + '/concat_vis_test.npz')


def test_pipeline_frank_fit():
    """Run the pipeline to perform a frank fit (and save fit diagnostics)"""

    # Default generic parameters file
    gen_pars = pipeline.load_default_parameters()

    gen_pars = update_frank_pars(gen_pars)

    gen_pars_file = save_custom_gen_pars(gen_pars)

    _run_pipeline(gen_pars_file)


def test_pipeline_frank_reproduce_bestfit():
    """Run the pipeline to perform a frank fit, using bestfit parameters in 'source_pars'"""

    # Default generic parameters file
    gen_pars = pipeline.load_default_parameters()

    gen_pars = update_frank_pars(gen_pars)
    gen_pars['base']['reproduce_best_frank'] = True
    gen_pars_file = save_custom_gen_pars(gen_pars)

    _run_pipeline(gen_pars_file)


def test_pipeline_frank_logfit():
    """Run the pipeline to perform a frank fit in log(brightness)"""

    gen_pars = pipeline.load_default_parameters()

    gen_pars = update_frank_pars(gen_pars)
    
    gen_pars['frank']['method'] = 'LogNormal'

    gen_pars_file = save_custom_gen_pars(gen_pars)

    _run_pipeline(gen_pars_file)


def test_pipeline_frank_multifit():
    """Run the pipeline to perform multiple frank fits and produce the multi-fit figures"""

    gen_pars = pipeline.load_default_parameters()

    gen_pars = update_frank_pars(gen_pars)

    gen_pars['base']['frank_multifit_fig'] = True
    gen_pars['frank']['alpha'] = [1.5, 1.3]

    gen_pars_file = save_custom_gen_pars(gen_pars)

    _run_pipeline(gen_pars_file)


def test_pipeline_frank_vertical_fit():
    """Run the pipeline to perform a frank fit with vertical inference"""

    gen_pars = pipeline.load_default_parameters()

    gen_pars = update_frank_pars(gen_pars)

    gen_pars['frank']['scale_height'] = 1e-1

    gen_pars_file = save_custom_gen_pars(gen_pars)

    _run_pipeline(gen_pars_file)


def test_pipeline_frank_vertical_multifit():
    """Run the pipeline to perform multiple frank fits with vertical inference and produce the aspect ratio figure"""

    gen_pars = pipeline.load_default_parameters()

    gen_pars = update_frank_pars(gen_pars)

    gen_pars['base']['aspect_ratio_fig'] = True
    # multiple values for scale_height will call np.logspace internally
    gen_pars['frank']['scale_height'] = [-2, 0, 3]

    gen_pars_file = save_custom_gen_pars(gen_pars)

    _run_pipeline(gen_pars_file)


def test_pipeline_extract_clean_profile():
    """Run the pipeline to extract a radial brightness profile from a clean image"""
    gen_pars = pipeline.load_default_parameters()

    gen_pars['base']['extract_clean_profile'] = True
    gen_pars['clean']['rmax'] = 2.0

    gen_pars_file = save_custom_gen_pars(gen_pars)

    _run_pipeline(gen_pars_file)
    

def test_pipeline_parametric_fit():
    """Run the pipeline to perform a parametric fit of a frank brightness profile
    over each of the supported parametric forms"""
    gen_pars = pipeline.load_default_parameters()

    gen_pars['base']['run_parametric'] = True
    gen_pars['parametric']['niter'] = 50

    for pp in ['gauss', 'asym_gauss', 'triple_gauss', 'double_powerlaw', 
               'double_powerlaw_erf', 'double_powerlaw_gauss', 'double_powerlaw_double_gauss',
               'single_erf_powerlaw', 'double_erf_powerlaw']:
        gen_pars['parametric']['form'] = pp

        gen_pars_file = save_custom_gen_pars(gen_pars)

        _run_pipeline(gen_pars_file)


def test_pipeline_model_comparison_figs():
    """Run the pipeline to produce figures comparing clean and frank bestfit models"""
    gen_pars = pipeline.load_default_parameters()

    gen_pars['base']['compare_models_fig'] = "clean, frank"

    gen_pars_file = save_custom_gen_pars(gen_pars)

    _run_pipeline(gen_pars_file)


def test_bulk_pipeline_run():
    """Run the pipeline to produce figures comparing clean and frank bestfit models"""
    gen_pars = pipeline.load_default_parameters()
    gen_pars_file = save_custom_gen_pars(gen_pars)
    source_pars_file = 'test/mockAS209/mock_pars_source.json'
    phys_pars_file = 'test/mockAS209/mock_pars_phys.csv'

    bulk_pipeline_run.main(gen_par_f=gen_pars_file,
                           source_par_f=source_pars_file,
                           phys_par_f=phys_pars_file,
                           )


def test_bulk_pipeline_results():
    """Run the pipeline to produce figures comparing clean and frank bestfit models"""
    gen_pars = pipeline.load_default_parameters()
    gen_pars_file = save_custom_gen_pars(gen_pars)
    source_pars_file = 'test/mockAS209/mock_pars_source.json'
    phys_pars_file = 'test/mockAS209/mock_pars_phys.csv'

    bulk_pipeline_results.main(gen_par_f=gen_pars_file,
                               source_par_f=source_pars_file, 
                               phys_par_f=phys_pars_file,
                               include_rave=False)


def test_analysis_belt_width():
    analysis.resolving_belt_width_figure('test/mockAS209/mock_pars_source.json',
                                         'test',
                                         os.path.join(tmp_dir, 'frank_resolving_belts.png')
                                         )
    

def test_aspect_ratio_trend():
    analysis.aspect_ratio_trend_figure('test/mockAS209/mock_aspect_ratios.txt',
                                       'test',
                                         os.path.join(tmp_dir, 'frank_aspect_ratio_trends.png')
                                         )
        