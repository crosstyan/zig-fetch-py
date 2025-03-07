```zon
.{
    .name = .zls,
    // Must match the `zls_version` in `build.zig`
    .version = "0.15.0-dev",
    // Must be kept in line with the `minimum_build_zig_version` in `build.zig`.
    // Should be a Zig version that is downloadable from https://ziglang.org/download/ or a mirror.
    .minimum_zig_version = "0.14.0",
    // If you do not use Nix, a ZLS maintainer can take care of this.
    // Whenever the dependencies are updated, run the following command:
    // ```bash
    // nix run github:Cloudef/zig2nix#zon2nix -- build.zig.zon > deps.nix
    // rm build.zig.zon2json-lock # this file is unnecessary
    // ```
    .dependencies = .{
        .known_folders = .{
            .url = "https://github.com/ziglibs/known-folders/archive/aa24df42183ad415d10bc0a33e6238c437fc0f59.tar.gz",
            .hash = "known_folders-0.0.0-Fy-PJtLDAADGDOwYwMkVydMSTp_aN-nfjCZw6qPQ2ECL",
        },
        .diffz = .{
            .url = "https://github.com/ziglibs/diffz/archive/ef45c00d655e5e40faf35afbbde81a1fa5ed7ffb.tar.gz",
            .hash = "N-V-__8AABhrAQAQLLLGadghhPsdxTgBk9N9aLVOjXW3ay0V",
        },
        .@"lsp-codegen" = .{
            .url = "https://github.com/zigtools/zig-lsp-codegen/archive/063a98c13a2293d8654086140813bdd1de6501bc.tar.gz",
            .hash = "lsp_codegen-0.1.0-CMjjo0ZXCQB-rAhPYrlfzzpU0u0u2MeGvUucZ-_g32eg",
        },
        .tracy = .{
            .url = "https://github.com/wolfpld/tracy/archive/refs/tags/v0.11.1.tar.gz",
            .hash = "N-V-__8AAMeOlQEipHjcyu0TCftdAi9AQe7EXUDJOoVe0k-t",
            .lazy = true,
        },
    },
    .paths = .{""},
    .fingerprint = 0xa66330b97eb969ae, // Changing this has security and trust implications.
}
```

It's called `zon`, the Zig Object Notation. I think You need to parse it first (convert to json) and then parse the json.
