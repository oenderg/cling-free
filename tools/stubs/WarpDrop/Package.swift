// swift-tools-version: 5.9
import PackageDescription

// Stand-in for upstream's private `WarpDrop` package, which is not published. Upstream's project
// references it as a local path (../../../Github/alin23/warpdrop/swift), so a clean checkout
// cannot even resolve its packages. unlock_pro.py repoints the project here.
let package = Package(
    name: "WarpDrop",
    platforms: [.macOS(.v12)],
    products: [.library(name: "WarpDrop", targets: ["WarpDrop"])],
    targets: [.target(name: "WarpDrop")]
)
