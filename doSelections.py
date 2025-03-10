import uproot as up4
import uproot3 as up3
import pandas as pd
import numpy as np
import boost_histogram as bh
import argparse
import glob
import gecorg as go

parser = argparse.ArgumentParser()

def boostUnc(values,weights,nbins,binstart,binstop):
    boosth = bh.Histogram(bh.axis.Regular(bins=nbins,start=binstart,stop=binstop),storage=bh.storage.Weight())
    boosth.fill(values,weight=weights)
    boostvar = boosth.view().variance
    boosterr = np.sqrt(boostvar)
    return boosterr

if __name__=='__main__':
    parser.add_argument("-f","--sample",help = "sample file")
    parser.add_argument("-o","--output",help = "output file name")
    parser.add_argument("-b","--btagger",help = "btagger selection, need name part of key")
    parser.add_argument("-wp","--btagWP",type=float,default=0.6,help = "doulbeB tagger working point (default M1)")
    parser.add_argument("-zpt","--zPtCut",type=float,default = 100.0,help = "pT cut on Z")
    parser.add_argument("-hpt","--hPtCut",type=float,default = 250.0,help = "pT cut on h")
    parser.add_argument("-met","--metPtCut",type=float,default = 50.0,help = "pT cut on met")
    parser.add_argument("-sdm","--sdmCut",type=float,default = 10.0,help = "lowest soft drop mass cut")
    parser.add_argument("-date","--date",type=str,help = "where are your topiary plots?")
    args = parser.parse_args()

    samp   = args.sample
    sdmcut = args.sdmCut
    zptcut = args.zPtCut
    hptcut = args.hPtCut
    metcut = args.metPtCut
    btaggr = args.btagger
    btagwp = args.btagWP

    #inputfiles = glob.glob('../RestFrames/analysis_output_ZpAnomalon/2020-12-29/'+samp+'*_topiary*.root')
    #inputfiles = glob.glob('../RestFrames/analysis_output_ZpAnomalon/'+args.date+'/'+samp+'*_topiary*.root')
    inputfiles = glob.glob('analysis_output_ZpAnomalon/'+args.date+'/'+samp+'*_topiary*.root')
    print("    Doing selections on:")
    print(inputfiles)
    stype,year = go.sampleType(samp)
    print(stype)
    
    branches = [b'ZCandidate_*',
                b'hCandidate_*',
                b'METclean',
                b'METPhiclean',
                b'ZPrime_mass_est',
                b'ND_mass_est',
                b'NS_mass_est',
                b'event_weight',
    ]

    
    #events = up3.iterate(inputfiles[:1],'PreSelection;1',branches=branches)
    events = up3.pandas.iterate(inputfiles[:1],'PreSelection;1',branches=branches)


    #print(events['event_weight'])
    
    #print(jets.ls))
    
    for b in events:
        #print(type(b))
        #print(b.keys())
        #print(b)
        #do some cuts
        sddf   = b[b['hCandidate_sd'] > sdmcut]
        metdf  = sddf[sddf['METclean'] > metcut]
        zptdf  = metdf[metdf['ZCandidate_pt'] > zptcut]
        hptdf  = zptdf[zptdf['hCandidate_pt'] > hptcut]
        btdf   = hptdf[hptdf['hCandidate_'+btaggr] > float(btagwp)]
        srup   = btdf[btdf['hCandidate_sd'] > 70.]
        srdf   = srup[srup['hCandidate_sd'] < 150.]
        lowsb  = btdf[btdf['hCandidate_sd'] <= 70.]
        highsb = btdf[btdf['hCandidate_sd'] >= 150.]
        sbdf   = pd.concat([lowsb,highsb])
        #btagging
        #btdf = srdf[srdf['hCandidate_'+btaggr] > float(btagwp)]

        #fdf is always the last dataframe
        #fdf = btdf
        if stype != 0:
            fdf = sbdf
        else:
            fdf = sbdf

        print("    number of passing events ",len(fdf))
        #print("number of btag passing events ",len(btdf))

    #lets make some histograms.
    rootfilename  = go.makeOutFile(samp,'upout_'+btaggr,'.root',str(zptcut),str(hptcut),str(metcut),str(btagwp))#need to update for btagger
    npfilename    = go.makeOutFile(samp,'totalevents_'+btaggr,'.npy',str(zptcut),str(hptcut),str(metcut),str(btagwp))
    pklfilename   = go.makeOutFile(samp,'selected_errors_'+btaggr,'.pkl',str(zptcut),str(hptcut),str(metcut),str(btagwp))
    rootOutFile   = up3.recreate(rootfilename,compression = None)
    npOutFile     = open(npfilename,'wb')

    rootOutFile["h_z_pt"]    = np.histogram(fdf['ZCandidate_pt'],bins=80,range=(0,800),weights=fdf['event_weight'])
    #rootOutFile["h_z_phi"]   = np.histogram(fdf['ZCandidate_phi'],bins=100,range=(0,3.14159),weights=fdf['event_weight'])#needs to fit range
    rootOutFile["h_z_eta"]   = np.histogram(fdf['ZCandidate_eta'],bins=100,range=(-5,5),weights=fdf['event_weight'])
    rootOutFile["h_z_m"]     = np.histogram(fdf['ZCandidate_m'],bins=100,range=(40,140),weights=fdf['event_weight'])
    rootOutFile["h_h_pt"]    = np.histogram(fdf['hCandidate_pt'],bins=40,range=(200,1200),weights=fdf['event_weight'])
    #rootOutFile["h_h_phi"]   = np.histogram(fdf['hCandidate_phi'],bins=100,range=(0,3.14159))#needs to fit range
    rootOutFile["h_h_eta"]   = np.histogram(fdf['hCandidate_eta'],bins=100,range=(-5,5),weights=fdf['event_weight'])
    rootOutFile["h_h_m"]     = np.histogram(fdf['hCandidate_m'],bins=80,range=(0,400),weights=fdf['event_weight'])
    rootOutFile["h_h_sd"]    = np.histogram(fdf['hCandidate_sd'],bins=80,range=(0,400),weights=fdf['event_weight'])
    rootOutFile["h_met"]     = np.histogram(fdf['METclean'],bins=78,range=(50,2000),weights=fdf['event_weight'])
    #rootOutFile["h_met_phi"] = np.histogram(fdf['METPhiclean'],bins=100,range=(0,3.14159))#needs to fit range
    rootOutFile["h_zp_jigm"] = np.histogram(fdf['ZPrime_mass_est'],bins=100,range=(500,5000),weights=fdf['event_weight'])
    rootOutFile["h_nd_jigm"] = np.histogram(fdf['ND_mass_est'],bins=70,range=(100,800),weights=fdf['event_weight'])
    rootOutFile["h_ns_jigm"] = np.histogram(fdf['NS_mass_est'],bins=50,range=(0,500),weights=fdf['event_weight'])
    rootOutFile["h_btag"]    = np.histogram(fdf['hCandidate_'+btaggr],bins=110,range=(0,1.1),weights=fdf['event_weight'])
    rootOutFile["h_weights"] = np.histogram(fdf['event_weight'],bins=40,range=(-1,7))

    zpterrs   = boostUnc(fdf['ZCandidate_pt'],fdf['event_weight'],80,0,800)
    zetaerrs  = boostUnc(fdf['ZCandidate_eta'],fdf['event_weight'],100,-5,5)
    zmerrs    = boostUnc(fdf['ZCandidate_m'],fdf['event_weight'],100,40,140)
    hpterrs   = boostUnc(fdf['hCandidate_pt'],fdf['event_weight'],40,200,1200)
    hetaerrs  = boostUnc(fdf['hCandidate_eta'],fdf['event_weight'],100,-5,5)
    hmerrs    = boostUnc(fdf['hCandidate_m'],fdf['event_weight'],80,0,400)
    hsderrs   = boostUnc(fdf['hCandidate_sd'],fdf['event_weight'],80,0,400)
    meterrs   = boostUnc(fdf['METclean'],fdf['event_weight'],28,50,2000)
    zpjigerrs = boostUnc(fdf['ZPrime_mass_est'],fdf['event_weight'],100,500,5000)
    ndjigerrs = boostUnc(fdf['ND_mass_est'],fdf['event_weight'],70,100,800)
    nsjigerrs = boostUnc(fdf['NS_mass_est'],fdf['event_weight'],50,0,500)
    btagerrs  = boostUnc(fdf['hCandidate_'+btaggr],fdf['event_weight'],110,0,1.1)

    unc_arrays = [zpterrs,
                  zetaerrs,
                  zmerrs,
                  hpterrs,
                  hetaerrs,
                  hmerrs,
                  hsderrs,
                  meterrs,
                  zpjigerrs,
                  ndjigerrs,
                  nsjigerrs,
                  btagerrs
    ]

    unc_names = ['h_z_pt',
                 'h_z_eta',
                 'h_z_m',
                 'h_h_pt',
                 'h_h_eta',
                 'h_h_m',
                 'h_h_sd',
                 'h_met',
                 'h_zp_jigm',
                 'h_nd_jigm',
                 'h_ns_jigm',
                 'h_btag'
    ]

    max_length = len(max(unc_arrays,key = lambda ar : len(ar)))
    pad_arrays = [np.pad(arr,(0,max_length - len(arr)),'constant') for arr in unc_arrays]
    all_unc    = np.column_stack(pad_arrays)
    uncdf      = pd.DataFrame(all_unc,columns=unc_names)
    uncdf.to_pickle("./"+pklfilename)
    
    #Book Keeping
    f = up3.open(inputfiles[0])
    np.save(npOutFile,np.array([f['hnorigevnts'].values[0]]))
    rootOutFile["hnevents"]      = str(f['hnorigevnts'].values[0])
    rootOutFile["hnevents_pMET"] = str(len(metdf))
    rootOutFile["hnevents_pZ"]   = str(len(zptdf))
    rootOutFile["hnevents_ph"]   = str(len(hptdf))
    rootOutFile["hnevents_sb"]   = str(len(sbdf))
    rootOutFile["hnevents_btag"] = str(len(btdf))
