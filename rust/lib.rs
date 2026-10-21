//! Bounded, zero-copy telemetry profile validation by Jason Stys.
//! Types/functions: Header, Inspection, inspect, inspect_hex, encode_hex.
//! Variables: primary-header words, declared size, payload limit and borrowed bytes.
//! Exact symbols/fields/locals: docs/CODE_INDEX.md. No unsafe code, CRC or authentication claim.

pub const HEADER_BYTES: usize = 6;
pub const MAX_PAYLOAD: usize = 4096;
pub const MAX_CAPTURE: u64 = 131_072;
pub const MAX_RECORDS: usize = 128;

/// Decoded big-endian primary header; data_length stores the encoded length-minus-one.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Header {
    pub version: u8,
    pub packet_type: u8,
    pub secondary: u8,
    pub apid: u16,
    pub flags: u8,
    pub sequence: u16,
    pub data_length: u16,
}

impl Header {
    /// Decode only after the caller proves six bytes exist; no struct casts or alignment assumptions.
    fn read(bytes: &[u8]) -> Self {
        let identification = u16::from_be_bytes([bytes[0], bytes[1]]);
        let sequence = u16::from_be_bytes([bytes[2], bytes[3]]);
        Self {
            version: (identification >> 13) as u8,
            packet_type: ((identification >> 12) & 1) as u8,
            secondary: ((identification >> 11) & 1) as u8,
            apid: identification & 0x7ff,
            flags: (sequence >> 14) as u8,
            sequence: sequence & 0x3fff,
            data_length: u16::from_be_bytes([bytes[4], bytes[5]]),
        }
    }

    /// Convert before addition: 65535 encodes 65536 data bytes, not zero.
    pub fn expected_size(self) -> usize {
        HEADER_BYTES + usize::from(self.data_length) + 1
    }
}

/// Inspection preserves a decoded header on rejection; payload is borrowed only on acceptance.
#[derive(Debug)]
pub struct Inspection<'a> {
    pub code: &'static str,
    pub header: Option<Header>,
    pub payload: &'a [u8],
}

/// Validate exactly one delimited record; error precedence is part of the public contract.
pub fn inspect(bytes: &[u8], payload_limit: usize) -> Inspection<'_> {
    if bytes.len() < HEADER_BYTES {
        return Inspection {
            code: "truncated-header",
            header: None,
            payload: &[],
        };
    }
    let header = Header::read(bytes);
    let code = if !(1..=MAX_PAYLOAD).contains(&payload_limit) {
        "invalid-profile-limit"
    } else if header.version != 0 {
        "unsupported-version"
    } else if bytes.len() != header.expected_size() {
        "length-mismatch"
    } else if usize::from(header.data_length) + 1 > payload_limit {
        "profile-payload-limit"
    } else if header.packet_type != 0 {
        "unsupported-packet-type"
    } else if header.secondary != 0 {
        "unsupported-secondary-header"
    } else if header.flags != 3 {
        "unsupported-segmentation"
    } else {
        "accepted"
    };
    Inspection {
        code,
        header: Some(header),
        payload: if code == "accepted" {
            &bytes[HEADER_BYTES..]
        } else {
            &[]
        },
    }
}

/// Render original bytes as lower-case hex, never text/markup or interpreted payload fields.
pub fn encode_hex(bytes: &[u8]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        output.push(DIGITS[usize::from(byte >> 4)] as char);
        output.push(DIGITS[usize::from(byte & 15)] as char);
    }
    output
}

/// Decode a bounded hex record; non-hex and odd input never allocate an unbounded buffer.
fn decode_hex(text: &str) -> Option<Vec<u8>> {
    if !text.len().is_multiple_of(2) {
        return None;
    }
    text.as_bytes()
        .as_chunks::<2>()
        .0
        .iter()
        .map(|pair| {
            let high = (pair[0] as char).to_digit(16)?;
            let low = (pair[1] as char).to_digit(16)?;
            Some((high * 16 + low) as u8)
        })
        .collect()
}

/// Emit fixed-key JSON without reflecting arbitrary input; no external serializer dependency.
pub fn inspect_hex(text: &str, payload_limit: usize) -> String {
    if text.len() > (HEADER_BYTES + MAX_PAYLOAD) * 2 {
        return record_error("record-too-large");
    }
    let Some(bytes) = decode_hex(text) else {
        return record_error("invalid-hex");
    };
    let result = inspect(&bytes, payload_limit);
    let header = if let Some(h) = result.header {
        format!(
            "{{\"version\":{},\"packet_type\":{},\"secondary\":{},\"apid\":{},\"flags\":{},\"sequence\":{},\"data_length\":{},\"expected_size\":{}}}",
            h.version,
            h.packet_type,
            h.secondary,
            h.apid,
            h.flags,
            h.sequence,
            h.data_length,
            h.expected_size()
        )
    } else {
        "null".to_owned()
    };
    format!(
        "{{\"code\":\"{}\",\"header\":{},\"actual_size\":{},\"payload_hex\":\"{}\"}}",
        result.code,
        header,
        bytes.len(),
        encode_hex(result.payload)
    )
}

/// Represent undecodable records without inventing a byte count or header.
fn record_error(code: &'static str) -> String {
    format!("{{\"code\":\"{code}\",\"header\":null,\"actual_size\":null,\"payload_hex\":\"\"}}")
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Golden manually constructed primary header; no production encoder serves as its own oracle.
    #[test]
    fn golden_and_borrowed_payload() {
        let bytes = [0x00, 0x2a, 0xc0, 0x01, 0x00, 0x02, 0xde, 0xad, 0xbe];
        let result = inspect(&bytes, 128);
        assert_eq!(result.code, "accepted");
        assert_eq!(
            result.header.unwrap(),
            Header {
                version: 0,
                packet_type: 0,
                secondary: 0,
                apid: 42,
                flags: 3,
                sequence: 1,
                data_length: 2
            }
        );
        assert_eq!(result.payload.as_ptr(), bytes[6..].as_ptr());
        assert_eq!(
            inspect_hex("002AC0010002DEADBE", 128),
            inspect_hex(&encode_hex(&bytes), 128)
        );
    }

    /// Exercise every identification word and independently extract fields using division/remainder.
    #[test]
    fn exhaustive_identification_words() {
        for word in 0..=u16::MAX {
            let [a, b] = word.to_be_bytes();
            let bytes = [a, b, 0xc0, 0, 0, 0, 1];
            let result = inspect(&bytes, 128);
            let h = result.header.unwrap();
            assert_eq!(u16::from(h.version), word / 8192);
            assert_eq!(u16::from(h.packet_type), (word / 4096) % 2);
            assert_eq!(u16::from(h.secondary), (word / 2048) % 2);
            assert_eq!(h.apid, word % 2048);
            assert_eq!(result.code == "accepted", word < 2048);
        }
    }

    /// Check all 65536 encoded lengths without overflow or trusting the declared body size.
    #[test]
    fn exhaustive_lengths() {
        for length in 0..=u16::MAX {
            let [a, b] = length.to_be_bytes();
            let bytes = [0, 42, 0xc0, 0, a, b];
            let result = inspect(&bytes, 128);
            assert_eq!(result.code, "length-mismatch");
            assert_eq!(
                result.header.unwrap().expected_size(),
                usize::from(length) + 7
            );
        }
        let mut largest = vec![0; 65542];
        largest[2] = 0xc0;
        largest[4] = 0xff;
        largest[5] = 0xff;
        assert_eq!(inspect(&largest, 4096).code, "profile-payload-limit");
    }

    /// Verify every supported boundary and each rejection branch; valid idle remains opaque.
    #[test]
    fn profile_edges() {
        for length in 0..6 {
            assert_eq!(inspect(&vec![0; length], 128).code, "truncated-header");
        }
        let mut bytes = vec![0, 42, 0xc0, 0, 0, 0, 1];
        assert_eq!(inspect(&bytes, 0).code, "invalid-profile-limit");
        bytes[0] = 0x10;
        assert_eq!(inspect(&bytes, 128).code, "unsupported-packet-type");
        bytes[0] = 0x08;
        assert_eq!(inspect(&bytes, 128).code, "unsupported-secondary-header");
        bytes[0] = 0;
        for flags in 0..3 {
            bytes[2] = flags << 6;
            assert_eq!(inspect(&bytes, 128).code, "unsupported-segmentation");
        }
        bytes[0] = 7;
        bytes[1] = 255;
        bytes[2] = 0xc0;
        assert_eq!(inspect(&bytes, 128).code, "accepted");
        assert!(inspect_hex("z1", 128).contains("invalid-hex"));
        assert!(inspect_hex("0", 128).contains("invalid-hex"));
        assert!(inspect_hex(&"00".repeat(4103), 128).contains("record-too-large"));
        assert!(inspect_hex("", 128).contains("truncated-header"));
        let mut maximum = vec![0; 4102];
        maximum[2] = 0xc0;
        maximum[4] = 15;
        maximum[5] = 255;
        assert_eq!(inspect(&maximum, 4096).payload.len(), 4096);
    }

    /// Deterministic hostile-byte fuzz campaign; acceptance implies exact size and supported fields.
    #[test]
    fn seeded_fuzz_50000_records() {
        let mut seed = 0x6b8b4567_u64;
        for index in 0..50_000 {
            let mut bytes = vec![0; index % 513];
            for byte in &mut bytes {
                seed = seed.wrapping_mul(6364136223846793005).wrapping_add(1);
                *byte = (seed >> 32) as u8;
            }
            let result = inspect(&bytes, 128);
            if result.code == "accepted" {
                let h = result.header.unwrap();
                assert_eq!(bytes.len(), h.expected_size());
                assert_eq!(h.version + h.packet_type + h.secondary, 0);
                assert_eq!(h.flags, 3);
                assert!(!result.payload.is_empty());
            }
            let encoded = encode_hex(&bytes);
            assert_eq!(decode_hex(&encoded).unwrap(), bytes);
            assert!(!inspect_hex(&encoded, 128).contains("NaN"));
        }
    }
}
