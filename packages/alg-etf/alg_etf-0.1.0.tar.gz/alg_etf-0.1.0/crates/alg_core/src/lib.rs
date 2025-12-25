// #![warn(
//     clippy::all,
//     clippy::restriction,
//     clippy::pedantic,
//     clippy::nursery,
//     clippy::cargo
// )]

//! This library aims to provide **Analog Circuit** designers tools to programatically implement planar
//! silicon structures without any limitations. It uses a high-performance hierachical layout
//! database with **Correct-by-Construction** DRC rules philosopy. This means the design created
//! inhearantly is complient with the DRC rules specified by the designer / technology file
//!
//! This library is ment to be used with bindings to python using PyO3
//!
//! This library creates GDSII files as output to be used with.

pub mod drc;
pub mod geo;
pub mod io;
pub mod library;
pub mod project;
