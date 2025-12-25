// Copyright (C) 2024- Davide Mollica <davide.mollica@inaf.it>
// SPDX-License-Identifier: GPL-3.0-or-later
//
// This file is part of iactsim.
//
// iactsim is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// iactsim is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with iactsim.  If not, see <https://www.gnu.org/licenses/>.

#include <iostream>
#include <chrono>
#include <cassert>

#include <IACTFile.h>

int main() {
  std::vector<std::string> files;

  int n_files = 8;
  printf("%d\n", n_files);
  for (int i=0; i<n_files; i++) {
    std::stringstream filename;
    // filename << "/media/davide/X9Pro/PhD/MiniprodHorn/proton/proton_20_20_180_180_run0200" 
    filename << "/media/davide/X9Pro/PhD/CORSIKA/MA/Prod2-Teide/proton/proton_20_20_000_000_run1000"
             << std::setw(2) << std::setfill('0') << i+80
             << ".corsika";
    filename << ".gz";
    std::cout << filename.str() << std::endl;
    files.push_back(filename.str());
  }

  double omp_start, omp_end;

  ///////////////
  // long int tot_size = 0;
  
  omp_start = omp_get_wtime();
  
  std::vector<iactxx::IACTFile> p_runs;
  p_runs.resize(n_files);

  
  #pragma omp parallel for default(none) shared(p_runs, files) firstprivate(n_files)
  for (int file_id=0; file_id<n_files; ++file_id)
  {
    auto file = files[file_id];
    iactxx::IACTFile corsikaRun;
    corsikaRun.setFilePath(file);
    corsikaRun.parseBunches();
    corsikaRun.convertBunches();
    p_runs[file_id] = std::move(corsikaRun);
  }
  omp_end = omp_get_wtime();
  std::cout << omp_end - omp_start << std::endl;

  // std::vector<IACTFile> p_runs;
  // p_runs.resize(n_files);
  // omp_start = omp_get_wtime();
  // #pragma omp parallel default(none) shared(files, n_files, p_runs)
  // {
  //   #pragma omp single
  //   {
  //     for (int file_id=0; file_id<n_files; ++file_id)
  //     {
  //       #pragma omp task
  //       {
  //         auto file = files[file_id];
  //         IACTFile corsikaRun;
  //         corsikaRun.setFilePath(file);
  //         corsikaRun.parseBunches();
  //         p_runs[file_id] = std::move(corsikaRun);
  //       }
  //     }
  //   }
  // }
  // omp_end = omp_get_wtime();
  // std::cout << omp_end - omp_start << std::endl;


  // for (auto& run:p_runs) {
  //   std::cout << "Pointing " << run.getPointing()[0] << " " << run.getPointing()[1] << std::endl;
  //   for (int tel_id=0; tel_id<9; tel_id++)
  //   // tot_size += run.getFileSize();
  //     tot_size += run.getNumberOfBunches(tel_id);
  // }
  // std::cout << tot_size << std::endl;

  ///////////////

  // std::vector<IACTFile> runs;
  // runs.resize(n_files);

  // omp_start = omp_get_wtime();
  // for (int file_id=0; file_id<n_files; ++file_id)
  // {
  //   auto file = files[file_id];
  //   IACTFile corsikaRun;
  //   corsikaRun.setFilePath(file);
  //   corsikaRun.parseBunches();
  //   runs[file_id] = std::move(corsikaRun);
  // }
  // omp_end = omp_get_wtime();
  // std::cout << omp_end - omp_start << std::endl;

  ///////////////
  
  // for (int k=0; k<n_files; ++k) {
  //   int n_events = runs[k].getNumberOfEvents();
  //   assert(n_events == p_runs[k].getNumberOfEvents());
    
  //   for (int event=0; event<n_events; ++event)
  //   {
  //     auto bunches = runs[k].getEventBunches(event);
  //     auto p_bunches = p_runs[k].getEventBunches(event);

  //     long int n = bunches.n_bunches;
  //     long int m = p_bunches.n_bunches;
  //     assert(n == m);
  //     for (long int i=0; i<n; ++i) {
  //       assert(p_bunches.pos[i].x      == bunches.pos[i].x);
  //       assert(p_bunches.pos[i].y      == bunches.pos[i].y);
  //       assert(p_bunches.dir[i].cx     == bunches.dir[i].cx);
  //       assert(p_bunches.dir[i].cy     == bunches.dir[i].cy);
  //       assert(p_bunches.zem[i]        == bunches.zem[i]);
  //       assert(p_bunches.time[i]       == bunches.time[i]);
  //       assert(p_bunches.wavelength[i] == bunches.wavelength[i]);
  //       assert(p_bunches.photons[i]    == bunches.photons[i]);
  //     }
  //   }
  // }

  // std::ofstream out;
  // out.open("event_bunches.txt");
  // for (int i=0; i<p_runs[n_files-1].getNumberOfEvents(); i++) {
  //   if (p_runs[n_files-1].getEventNumberOfBunches(0, i) > 20000) {
  //     std::cout << p_runs[n_files-1].getEventNumberOfBunches(0, i) << std::endl;
  //     out << p_runs[n_files-1].getEventBunches(0, i) << std::endl;
  //     break;
  //   }
  // }
  // out.close();

  // std::ofstream out;
  // out.open("event_bunches.txt");
  // for (int i=0; i<p_runs[2].getNumberOfEvents(); i++) {
  //   if (i < 1000) {
  //     std::cout << p_runs[2].getEventNumberOfBunches(0, i) << std::endl;
  //     out << p_runs[2].getEventBunches(0, i) << std::endl;
  //   }
  // }
  // out.close();

  return 0;
}