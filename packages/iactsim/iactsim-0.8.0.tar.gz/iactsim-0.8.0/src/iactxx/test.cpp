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
    std::string file_zst = "/media/davide/X9Pro/PhD/CORSIKA/MA/Prod2-Teide/muons/run100000_muon_za0deg_azm180deg.corsika.zst";
    std::string file_gzip = "/media/davide/X9Pro/PhD/CORSIKA/MA/Prod2-Teide/muons/run100000_muon_za0deg_azm180deg.corsika.gz";

    std::cout << "ZSTD File " << std::endl;
    iactxx::IACTFile cfile_zst;
    cfile_zst.setFilePath(file_zst);
    cfile_zst.parseBunches();
    cfile_zst.convertBunches();

    std::cout << "GZ File " << std::endl;
    iactxx::IACTFile cfile_gz;
    cfile_gz.setFilePath(file_gzip);
    cfile_gz.parseBunches();
    cfile_gz.convertBunches();

    std::string file_p_zst = "/media/davide/X9Pro/PhD/CORSIKA/MA/test_decompression/proton_20_20_000_000_run100082.corsika.zst";
    std::string file_p_gzip = "/media/davide/X9Pro/PhD/CORSIKA/MA/test_decompression/proton_20_20_000_000_run100082.corsika.gz";

    std::cout << "ZSTD File " << std::endl;
    iactxx::IACTFile cfile_p_zst;
    cfile_p_zst.setFilePath(file_p_zst);
    cfile_p_zst.parseBunches();
    cfile_p_zst.convertBunches();

    std::cout << "GZ File " << std::endl;
    iactxx::IACTFile cfile_p_gz;
    cfile_p_gz.setFilePath(file_p_gzip);
    cfile_p_gz.parseBunches();
    cfile_p_gz.convertBunches();

    return 0; 
}