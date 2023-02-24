{
  description = "ha-prometheus-sensor";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs";
  inputs.pre-commit-hooks.url = "github:cachix/pre-commit-hooks.nix";
  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs = { self, nixpkgs, pre-commit-hooks, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      {
        checks = {
          pre-commit-check = pre-commit-hooks.lib.${system}.run {
            src = ./.;
            hooks = {
              black.enable = true;
              isort.enable = true;
              ruff.enable = true;
            };
          };
        };
        devShells.default = with nixpkgs.legacyPackages.${system}; mkShell {
          inherit (self.checks.${system}.pre-commit-check) shellHook;

          buildInputs = [
            black
            isort
            mypy
            ruff
          ] ++ (with python3.pkgs; [
            # typing stubs
            aiohttp
            homeassistant-stubs
            voluptuous-stubs
          ]);
        };
      }
    );
}
