#include "TCanvas.h"
#include "TFile.h"
#include "TH1F.h"
#include "TString.h"

void plot(int runnr) {
  gStyle->SetOptStat(0);

  stringstream ss_number;
  ss_number << setw(6)<< setfill( '0' )  << runnr;
  string s_number = ss_number.str();
  TString number = s_number;
  TString input_file = "Run";
  input_file += number;
  input_file += "_SCurve.root";

  TFile *infile = TFile::Open(input_file);

  TString foldername = "Detector/Board_0/OpticalGroup_0/";
  infile->cd(foldername);
  TDirectory* dir = gDirectory;
  TIter iter(dir->GetListOfKeys()); // list of hybrids
  TKey *key;

  vector<TString> modules = {};
  while ((key = (TKey*)iter())) {
    TString name = key->ReadObj()->GetName();
    modules.emplace_back(name);
    cout << "name: " << name << endl;
  }
  for(size_t i=0; i<modules.size(); i++){

    TString module = modules[i];
    TString histpath = foldername + module;
    infile->cd();
    infile->cd(histpath);
    TDirectory* dir2 = gDirectory;
    TIter iter2(dir2->GetListOfKeys()); // list of hybrids
    TKey *key2;

    vector<TString> chips = {};
    while ((key2 = (TKey*)iter2())) {
      TString name2 = key2->ReadObj()->GetName();
      chips.emplace_back(name2);
      cout << "name2: " << name2 << endl;
    }

    vector<TCanvas*> h_scurves = {};
    vector<TCanvas*> h_threshs = {};
    vector<TCanvas*> h_noises = {};

    TString canvastitle_scurves = "Run";
    canvastitle_scurves += number;
    canvastitle_scurves += "_SCurves_" + module;
    //canvastitle_scurves += i+1;
    TCanvas* c_scurve = new TCanvas("c_scurve", canvastitle_scurves, 1000, 1000);
    c_scurve->Divide(2,2);

    TString canvastitle_threshs = "Run";
    canvastitle_threshs += number;
    canvastitle_threshs += "_Thresholds_" + module;
    //canvastitle_threshs += i+1;
    TCanvas* c_thresh = new TCanvas("c_thresh", canvastitle_threshs, 1000, 1000);
    c_thresh->Divide(2,2);

    TString canvastitle_noises = "Run";
    canvastitle_noises += number;
    canvastitle_noises += "_Noises_" + module;
    //canvastitle_noises += i+1;
    TCanvas* c_noise = new TCanvas("c_noise", canvastitle_noises, 1000, 1000);
    c_noise->Divide(2,2);

    for(size_t j=0; j<chips.size(); j++){
      TString chip = chips[j];
      TString mod_dummy = module;
      TString chip_dummy = chip;
      TString fullhistpath = histpath + "/" + chip;


      TString histname_scurve = "D_B(0)_O(0)_H(" + mod_dummy.ReplaceAll("Hybrid_", "") + ")_SCurves_Chip(" + chip_dummy.ReplaceAll("Chip_", "") + ")";
      TString canvasname_scurve = fullhistpath + "/" + histname_scurve;
      TCanvas* c_scurve_tmp = (TCanvas*)infile->Get(canvasname_scurve);
      TH1F* scurve_tmp = (TH1F*)c_scurve_tmp->GetPrimitive(histname_scurve);

      TString canvastitle_scurves_sing = canvastitle_scurves + "_" + chip;
      TCanvas* c_scurve_sing = new TCanvas("c_scurve_sing", canvastitle_scurves_sing, 500, 500);
      gPad->SetLogz();
      scurve_tmp->Draw("colz");
      c_scurve_sing->SaveAs(canvastitle_scurves_sing + ".pdf");
      c_scurve_sing->SaveAs(canvastitle_scurves_sing + ".png");

      // (TH1F*)c_scurve_tmp->GetPrimitive(histname_scurve);
      // c_scurve->cd(j+1);
      // gPad->SetLogz();
      // scurve_tmp->Draw("colz");


      TString histname_thresh = "D_B(0)_O(0)_H(" + mod_dummy.ReplaceAll("Hybrid_", "") + ")_Threshold1D_Chip(" + chip_dummy.ReplaceAll("Chip_", "") + ")";
      TString canvasname_thresh = fullhistpath + "/" + histname_thresh;
      TCanvas* c_thresh_tmp = (TCanvas*)infile->Get(canvasname_thresh);
      TH1F* thresh_tmp = (TH1F*)c_thresh_tmp->GetPrimitive(histname_thresh);

      TString canvastitle_threshs_sing = canvastitle_threshs + "_" + chip;
      TCanvas* c_thresh_sing = new TCanvas("c_thresh_sing", canvastitle_threshs_sing, 500, 500);
      thresh_tmp->Draw();
      c_thresh_sing->SaveAs(canvastitle_threshs_sing + ".pdf");
      c_thresh_sing->SaveAs(canvastitle_threshs_sing + ".png");

      // thresh_tmp = (TH1F*)c_thresh_tmp->GetPrimitive(histname_thresh);
      // c_thresh->cd(j+1);
      // thresh_tmp->Draw();

      TString histname_noise = "D_B(0)_O(0)_H(" + mod_dummy.ReplaceAll("Hybrid_", "") + ")_Noise1D_Chip(" + chip_dummy.ReplaceAll("Chip_", "") + ")";
      TString canvasname_noise = fullhistpath + "/" + histname_noise;
      TCanvas* c_noise_tmp = (TCanvas*)infile->Get(canvasname_noise);
      TH1F* noise_tmp = (TH1F*)c_noise_tmp->GetPrimitive(histname_noise);

      TString canvastitle_noises_sing = canvastitle_noises + "_" + chip;
      TCanvas* c_noise_sing = new TCanvas("c_noise_sing", canvastitle_noises_sing, 500, 500);
      noise_tmp->Draw();
      c_noise_sing->SaveAs(canvastitle_noises_sing + ".pdf");
      c_noise_sing->SaveAs(canvastitle_noises_sing + ".png");

      // noise_tmp = (TH1F*)c_noise_tmp->GetPrimitive(histname_noise);
      // c_noise->cd(j+1);
      // noise_tmp->Draw();
    }
    // c_scurve->SaveAs(canvastitle_scurves + ".pdf");
    // c_scurve->SaveAs(canvastitle_scurves + ".png");
    // c_thresh->SaveAs(canvastitle_threshs + ".pdf");
    // c_thresh->SaveAs(canvastitle_threshs + ".png");
    // c_noise->SaveAs(canvastitle_noises + ".pdf");
    // c_noise->SaveAs(canvastitle_noises + ".png");
  }

}
