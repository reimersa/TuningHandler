void readoutpixelmap(TString start, TString stop, int nruns){

  gStyle->SetOptStat(0);
  cout << "start: " << start << endl;
  cout << "stop: " << stop << endl;
  cout << "nruns: " << nruns << endl;

  vector<int> board_no = {0};
  vector<int> group_no = {0};
  vector<int> hybrid_no = {1};
  vector<int> chip_no = {0,1,2,3};
  // int nruns = 50;


  TString infilename = "../plots/source_scans_averaged/combined_" + start + "_" + stop + "_";
  infilename += nruns;
  infilename += ".root";
  TFile* infile = new TFile(infilename, "READ");

  for(auto const& board: board_no) {
    for(auto const& group: group_no) {
      for(auto const& hybrid: hybrid_no) {
	for(auto const& chip: chip_no) {

	  std::cout << "board = " << board << ", group = " << group << " " << ", hybrid = " << hybrid << ", chip = " << chip << std::endl;


	  TString foldername = "combined/Detector/Board_";
	  foldername += board;
	  foldername += "/OpticalGroup_";
	  foldername += group;
	  foldername += "/Hybrid_";
	  foldername += hybrid;
	  foldername += "/Chip_";
	  foldername += chip;
	  cout << "foldername: " << foldername << endl;
	  
	  TString histname = "D_B(";
	  histname += board;
	  histname += ")_O(";
	  histname += group;
	  histname += ")_H(";
	  histname += hybrid;
	  histname += ")_PixelAlive_Chip(";
	  histname += chip;
	  histname += ")";
	  cout << "histname: " << histname << endl;


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
	  TString replacewith = "_pixelmap_board";
	  replacewith += board;
	  replacewith += "_group";
	  replacewith += group;
	  replacewith += "_hybrid";
	  replacewith += hybrid;
	  replacewith += "_chip";
	  replacewith += chip;
	  replacewith += ".pdf";
	  outfilename.ReplaceAll(".root", replacewith);
	  c->SaveAs(outfilename);

	  
	}
      }
    }
  }
  
}
