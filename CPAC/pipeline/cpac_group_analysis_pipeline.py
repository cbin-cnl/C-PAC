import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.io as nio

import re
import os
import sys
import glob

from CPAC.utils.datasource import create_gpa_dataflow


def prep_group_analysis_workflow(c, resource, subject_infos):
    print 'Preparing Group Analysis workflow'
    print 'subjects', subject_infos
    
    p_id, s_ids, scan_ids, s_paths = (list(tup) for tup in zip(*subject_infos))
    
    if c.mixed_scan_analysis == True:
        wf = pe.Workflow(name = 'group_analysis_%s'%resource)
    else:
        wf = pe.Workflow(name = 'group_analysis_%s_%s'%resource%scan_ids[0]) 
    
    wf.base_dir = c.workingDirectory
    
    #extract model files
    model_list = [line.rstrip('\r\n') for line in open(c.modelFile, 'r')]
    
    if not model_list:
        raise Exception("mode_list is empty. Please provide" \
                         "a model file with full paths of the" \
                         "folder containing models for group analysis")
    
    from collections import defaultdict
    model_map = defaultdict(list)
    
    #create a map of model as key and its sub files as values
    for model in model_list:
        if os.path.exists(model):
            files = glob.glob(os.path.join(model, '*'))
            model_map[os.path.basename(model)] = files
        else:
            raise Exception ("Path to the model %s doesn't exist"%model)
    
    print model_map
    gp_flow = create_gpa_dataflow(model_map, c.ftest)
    
    from CPAC.group_analysis import create_group_analysis
    
    gpa_wf = create_group_analysis(c.ftest)
    gpa_wf.inputs.inputspec.zmap_files = s_paths
    
    wf.connect(gp_flow, 'outputspec.mat',
               gpa_wf, 'inputspec.mat_file')
    wf.connect(gp_flow, 'outputspec.con',
               gpa_wf, 'inputspec.con_file')
    wf.connect(gp_flow, 'outputspec.grp',
                gpa_wf, 'inputspec.grp_file')
        
    if c.fTest:
        workflow.connect(gp_flow, 'outputspec.fts',
                         gpa_wf, 'inputspec.fts_file') 
    
    ds = pe.Node(nio.DataSink(), name='gpa_sink')
    out_dir = os.path.dirname(s_paths[0]).replace(s_ids[0], 'group_analyis_results')
    ds.inputs.base_directory = out_dir
    ds.inputs.container = resource
    
    wf.run(plugin='MultiProc',
                         plugin_args={'n_procs': c.numCoresPerSubject})

    



if __name__ == "__main__":
    import argparse
    import re
    import commands
    commands.getoutput('source ~/.bashrc')
    import os
    import sys
    import pickle

    parser = argparse.ArgumentParser()
    
    parser.add_argument('-c', '--config',
                        dest='config',
                        required=True,
                        help='location of config file'
                        )
    
    parser.add_argument('-i', '--subject_infos',
                        dest='subject_infos',
                        required=True,
                        help='subject_info'
                        )

    parser.add_argument('-r', '--resource',
                        dest='resource',
                        required=True,
                        help='resource'
                        )


    
    args = parser.parse_args()
    path, fname = os.path.split(os.path.realpath(args.config))
    sys.path.append(path)
    c = __import__(fname.split('.')[0])


    prep_group_analysis_workflow(c, pickle.load(open(args.resource, 'r') ), pickle.load(open(args.subject_infos, 'r')))

