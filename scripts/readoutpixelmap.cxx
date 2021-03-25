void readoutpixelmap(TString start, TString stop, int nruns){

  gStyle->SetOptStat(0);
  cout << "start: " << start << endl;
  cout << "stop: " << stop << endl;
  cout << "nruns: " << nruns << endl;

  int board_no = 0;
  int group_no = 0;
  int hybrid_no = 1;
  int chip_no = 1;
  // int nruns = 50;

  TString foldername = "combined/Detector/Board_";
  foldername += board_no;
  foldername += "/OpticalGroup_";
  foldername += group_no;
  foldername += "/Hybrid_";
  foldername += hybrid_no;
  foldername += "/Chip_";
  foldername += chip_no;
  cout << "foldername: " << foldername << endl;

  TString histname = "D_B(";
  histname += board_no;
  histname += ")_O(";
  histname += group_no;
  histname += ")_H(";
  histname += hybrid_no;
  histname += ")_PixelAlive_Chip(";
  histname += chip_no;
  histname += ")";
  cout << "histname: " << histname << endl;

  TString infilename = "combined_" + start + "_" + stop + "_";
  infilename += nruns;
  infilename += ".root";
  TFile* infile = new TFile(infilename, "READ");

  TH2D* h = (TH2D*)infile->Get(foldername + "/" + histname);
  h->Scale((float)1./nruns);

  for(unsigned int ix=1; ix<h->GetNbinsX()+1; ix++){
    for(unsigned int iy=1; iy<h->GetNbinsY()+1; iy++){
      if(h->GetBinContent(ix, iy) > 1E-6) h->SetBinContent(ix, iy, 0);
    }
  }
  h->SetMaximum(5E-9);


  TCanvas* c = new TCanvas();
  h->Draw("colz");
  h->GetZaxis()->SetTitle("Average pixel occupancy");
  gPad->SetRightMargin(0.15);
  TPaletteAxis* pa = (TPaletteAxis*)h->GetListOfFunctions()->FindObject("palette");
  pa->SetX1NDC(0.87);
  pa->SetX2NDC(0.91);
  gPad->SetTickx();
  gPad->SetTicky();

  TString outfilename = infilename;
  TString replacewith = "_pixelmap_chip";
  replacewith += chip_no;
  replacewith += ".pdf";
  outfilename.ReplaceAll(".root", replacewith);
  c->SaveAs(outfilename);
}
