{
  description = "Fetch a Song from USDB";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
  }:
    flake-utils.lib.eachDefaultSystem (
      system: let
        pkgs = import nixpkgs {inherit system;};

        python = pkgs.python3;

        pname = "usdb-fetcher";

        usdbFetcher = python.pkgs.buildPythonApplication {
          src = pkgs.lib.cleanSource ./.;

          name = pname;

          format = "pyproject";

          propagatedBuildInputs = with python.pkgs; [
            pip
            setuptools
            yt-dlp
            pkgs.ffmpeg
            beautifulsoup4
            requests
          ];
        };
      in {
        packages.default = usdbFetcher;
        packages.rodeonix = usdbFetcher;
      }
    );
}
