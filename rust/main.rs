//! Fixed-input bounded worker CLI by Jason Stys; stdin is a lab hex-record capture, not RF.
//! Functions: run, main. Variables: payload limit, capture bytes, record lines and output rows.
//! Trusted record boundaries provide recovery; no byte scanning guesses a new CCSDS boundary.
//! Definition/variable locations: docs/CODE_INDEX.md.

use ccsds_telemetry_integrity_lab::{MAX_CAPTURE, MAX_RECORDS, inspect_hex};
use std::io::{self, Read, Write};

/// Read at most 128 KiB and 128 records; validate the complete envelope before emitting evidence.
fn run() -> Result<(), &'static str> {
    let args: Vec<String> = std::env::args().skip(1).collect();
    if args.len() != 1 {
        return Err("Usage: telemetry-core <32|128|4096> < capture.hex");
    }
    let limit: usize = args[0].parse().map_err(|_| "Invalid profile limit")?;
    if ![32, 128, 4096].contains(&limit) {
        return Err("Invalid profile limit");
    }
    let mut input = Vec::new();
    io::stdin()
        .take(MAX_CAPTURE + 1)
        .read_to_end(&mut input)
        .map_err(|_| "Cannot read capture")?;
    if input.len() as u64 > MAX_CAPTURE {
        return Err("Capture exceeds 128 KiB");
    }
    let text = std::str::from_utf8(&input).map_err(|_| "Capture must be ASCII hex records")?;
    if !text.is_ascii() {
        return Err("Capture must be ASCII hex records");
    }
    let lines: Vec<&str> = text
        .split_terminator('\n')
        .map(|line| line.strip_suffix('\r').unwrap_or(line))
        .collect();
    if lines.len() > MAX_RECORDS {
        return Err("Capture exceeds 128 records");
    }
    let mut output = io::BufWriter::new(io::stdout().lock());
    for line in lines {
        writeln!(output, "{}", inspect_hex(line, limit)).map_err(|_| "Cannot write evidence")?;
    }
    output.flush().map_err(|_| "Cannot flush evidence")
}

/// Return a controlled failure without echoing input, paths or panic details.
fn main() {
    if let Err(error) = run() {
        eprintln!("{error}");
        std::process::exit(2);
    }
}
