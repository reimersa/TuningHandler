void CopyDir(TDirectory *source) {
  //copy all objects and subdirs of directory source as a subdir of the current directory
  //  source->ls();
  TDirectory *savdir = gDirectory;

  string dname = (string)source->GetName();

  if (dname.find(".root")!=std::string::npos){
    dname = "combined";
  }
    

  TDirectory *adir;

  if(savdir->GetDirectory((TString)dname)==0){
    adir = savdir->mkdir((TString)dname);
  }else{
    adir = savdir->GetDirectory((TString)dname); 
  }

  adir->cd();

  //  adir->cd();
  //loop on all entries of this directory
  TKey *key;
  TIter nextkey(source->GetListOfKeys());
  while ((key = (TKey*)nextkey())) {
    const char *classname = key->GetClassName();
    TClass *cl = gROOT->GetClass(classname);
    if (!cl) continue;
    if (cl->InheritsFrom(TDirectory::Class())) {
      source->cd(key->GetName());
      TDirectory *subdir = gDirectory;
      adir->cd();
      CopyDir(subdir);
      adir->cd();
    } else if (cl->InheritsFrom(TTree::Class())) {
      TTree *T = (TTree*)source->Get(key->GetName());
      adir->cd();
      TTree *newT = T->CloneTree(-1,"fast");
      newT->Write();
    } else if (cl->InheritsFrom(TCanvas::Class())) {

      TCanvas *C = (TCanvas*)source->Get(key->GetName());
      adir->cd();

      string oname = (string)C->GetName();

      // only save pixel alive for now ... 
      if (oname.find("PixelAlive")==std::string::npos) continue; 

      TH2F* hist = (TH2F*)C->GetPrimitive((TString)oname);

      //extract histogram
      hist->Write();
    } else {
      source->cd();
      TObject *obj = key->ReadObj();
      adir->cd();
      obj->Write();
      delete obj;
    }
  }
  adir->SaveSelf(kTRUE);
  savdir->cd();
}





void CopyFile(const char *fname) {
  //Copy all objects and subdirs of file fname as a subdir of the current directory
  TDirectory *target = gDirectory;
  TFile *f = TFile::Open(fname);
  if (!f || f->IsZombie()) {
    printf("Cannot copy file: %s\n",fname);
    target->cd();
    return;
  }
  target->cd();
  CopyDir(f);
  delete f;
  target->cd();
}
void copyFiles(TString input, TString output) {

  //main function copying 4 files as subdirectories of a new file
  TFile *f = new TFile(output,"recreate");
  //  CopyFile("Run000321_NoiseScan.root");
  CopyFile(input);
  f->ls();

  delete f;
}


