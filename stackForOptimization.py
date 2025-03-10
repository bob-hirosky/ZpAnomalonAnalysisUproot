import argparse
import ROOT
import glob
import os
import gecorg
import numpy as np
from datetime import date
from ROOT import kOrange, kViolet, kCyan, kGreen, kPink, kAzure, kMagenta, kBlue, kBird
from math import sqrt

if __name__=='__main__':
    #build module objects
    parser = argparse.ArgumentParser()

    #Define parser imputs
    parser.add_argument("-L","--lumi", type=float,default = 137, help = "integrated luminosity for scale in fb^-1")
    parser.add_argument("-x","--xsec", type=float,help = "desired siganl cross section in fb")
    parser.add_argument("-p","--plot", type=str,help = "desired plot name to make the optimization for")
    parser.add_argument("-m","--metcut", type=float,help = "met cut of samples")
    parser.add_argument("-z","--zptcut", type=float,help = "zpt cut of samples")
    parser.add_argument("-j","--hptcut", type=float,help = "hpt cut of samples")
    parser.add_argument("-date","--date",help="date folder with plots to stack")
    parser.add_argument("-wp","--btagwp", type=float,help = "btag working point")
    parser.add_argument("-y","--year", type=float,help = "year of samples eg. 2017 -> 17")
    args = parser.parse_args()

    #Get command line parameters
    lumi          = args.lumi
    sig_xsec      = args.xsec
    released_plot = args.plot
    zptcut        = args.zptcut
    hptcut        = args.hptcut
    metcut        = args.metcut
    btagwp        = args.btagwp
    year          = args.year
    plotmax       = 100.0
    #Samples
    bkgfiles = gecorg.gatherBkg('analysis_output_ZpAnomalon/'+args.date+'/','upout',zptcut,hptcut,metcut,btagwp,year)
    bkgnames = ["DYJetsToLL","TT","WZTo2L2Q","ZZTo2L2Q"]
    sigfiles = glob.glob('analysis_output_ZpAnomalon/'+args.date+'/Zp*_Zptcut'+str(zptcut)+'_Hptcut'+str(hptcut)+'_metcut'+str(metcut)+'_btagwp'+str(btagwp)+'.root')

    #Prep signals
    sig_colors = gecorg.colsFromPalette(sigfiles,ROOT.kCMYK)
    sig_info   = gecorg.prepSig(sigfiles,sig_colors,sig_xsec,lumi)

    #Prep backgrounds
    bkg_colors = gecorg.colsFromPalette(bkgnames,ROOT.kLake)
    bkg_info   = gecorg.prepBkg(bkgfiles,bkgnames,bkg_colors,'xsects_2017.ini',lumi,"yes")
    #Make the stacked plot
    hname = released_plot
    leg = ROOT.TLegend(0.45,0.55,0.90,0.88)
    hsbkg = ROOT.THStack('hsbkg','')
    #gecorg.stackBkg(bkg_info,released_plot,hsbkg,leg,10000000,0.1)
    gecorg.stackBkg(bkg_info,released_plot,hsbkg,leg,plotmax,0.0)


    #LUT with titles
    titles = {
        "h_z_pt":"Z pT",
        "h_h_pt":"Higgs pT",
        "h_h_sd":"Higgs Soft Drop Mass",
        "h_met":"pT miss",
        "h_zp_jigm":"Jigsaw Mass Estimator Z'",
        "h_nd_jigm":"Jigsaw Mass Estimator ND",
        "h_btag":"btag point"
        }

    #Make a multigraph
    mg = ROOT.TMultiGraph()
                
    #Prep the pads
    tc = ROOT.TCanvas("tc",hname,600,800)
    p1 = ROOT.TPad("p1","stack_"+hname,0,0.4,1.0,1.0)
    #p1.SetLogy()
    #p1.SetBottomMargin(0)
    p1.SetLeftMargin(0.15)
    p1.SetRightMargin(0.05)
    p2 = ROOT.TPad("p2","signif_"+hname,0,0.0,1.0,0.4)
    #p2.SetTopMargin(0)
    p2.SetRightMargin(.05)
    p2.SetLeftMargin(0.15)
    p2.SetBottomMargin(0.2)

    #Prepare first pad for stack
    p1.Draw()
    p1.cd()

    #Draw the stack
    hsbkg.Draw("HIST")#add PFC for palette drawing
    hsbkg.GetXaxis().SetTitle(titles[hname])
    hsbkg.GetXaxis().SetTitleSize(0.05)
    hsbkg.GetYaxis().SetTitle("Events")
    hsbkg.GetYaxis().SetTitleSize(0.05)
    tc.Modified()
    
    #Add the signal plots
    max_max = 0
    for p,masspoint in enumerate(sig_info):
        #print "def saw ",masspoint["name"]
        #if p == 1:
        #    break
        hsig = masspoint["tfile"].Get(hname)
        hsig.SetStats(0)
        hsig.Scale(masspoint["scale"])
        hsig.SetLineColor(masspoint["color"])
        hsig.SetLineWidth(2)
        #hsig.SetMaximum(10000000)
        hsig.SetMaximum(plotmax)
        #hsig.SetMinimum(0.1)
        #hsig.SetMinimum(0.1)
        hsig.Draw("HISTSAME")
        leg.AddEntry(hsig,"Zp"+str(masspoint["mzp"])+" ND"+str(masspoint["mnd"])+" NS"+str(masspoint["mns"])+" "+str(sig_xsec/1000)+" pb","l")
        
        #Now the significance calculation
        hsum = hsbkg.GetStack().Last()
        cutlist = np.zeros(hsum.GetNbinsX())
        signiflist = np.zeros(hsum.GetNbinsX())

        for ibin in range(hsum.GetNbinsX()):
            theocut = hsum.GetBinLowEdge(ibin)
            bkg_sig = 0
            sig     = 0
            for b in range(ibin,hsum.GetNbinsX()):
                bkg_sig += hsum.GetBinContent(b)+hsig.GetBinContent(b)
                sig     += hsig.GetBinContent(b)

            if bkg_sig == 0.0:
                signif = 0.0
            else:
                signif           = sig/sqrt(bkg_sig)
                signiflist[ibin] = signif
            cutlist[ibin]    = theocut

        #remove underflow bin
        signiflist = np.delete(signiflist,0)
        cutlist    = np.delete(cutlist,0)

        #Debug
        #print signiflist
        #print cutlist

        #Build the graphs
        tg = ROOT.TGraph(hsum.GetNbinsX()-1,cutlist,signiflist)
        tg.SetTitle(titles[hname])
        tg.SetLineWidth(2)
        tg.SetLineColor(masspoint["color"])
        #tg.SetLineStyle(masspoint["style"])
        mg.Add(tg)

        #Make the second pad with the significance plot
        tc.cd()
        p2.Draw()
        p2.cd()
        mg.Draw("AL")
        #Now, the beauty aspects
        #print signiflist
        temp_max = np.amax(signiflist)
        if temp_max > max_max:
            max_max = temp_max
            
        mg.SetTitle("")
        #x axis
        mg.GetXaxis().SetTitle("cut value")
        mg.GetXaxis().SetTitleSize(0.07)
        mg.GetXaxis().SetLabelSize(0.05)
        mg.GetXaxis().SetLimits(cutlist[0],cutlist[-1]+hsum.GetBinWidth(1))
        #y axis
        mg.GetYaxis().SetTitle("S/#sqrt{B+S} a.u.")
        mg.GetYaxis().SetTitleSize(0.07)
        mg.GetYaxis().SetTitleOffset(.7)
        mg.GetYaxis().SetLabelSize(0.05)
        mg.SetMinimum(0)
        mg.SetMaximum(30)
        
        #Go back to previous pad so next kinematic plots draw
        tc.cd()
        p1.cd()

    #Draw the legent with everything added
    leg.SetBorderSize(0)
    leg.Draw()

    #Save the plot
    pngname = gecorg.makeOutFile(hname,'optimization','.png',str(zptcut),str(hptcut),str(metcut),str(btagwp))
    tc.SaveAs(pngname)
