# APID continuity review

Expand an APID to see its accepted-record timeline and provisional gap intervals. Click a record to inspect the original parser/continuity evidence. A gap records counters absent between advancing baselines; it is not proof of permanently lost data. Intervals are compressed modulo 16384, keeping memory bounded by the 128-record capture rather than the counter gap size.

An accepted **late-or-reset** counter that uniquely matches a provisional range in the current review segment is recorded as an observed late recovery. The same counter observed again does not count twice. This is counter recovery only: payload authenticity, equivalent content and actual sender session identity remain unknown. The original record's disposition, high-water baseline and original `totals.unobserved_values` never change.

Unmatched late/reset records, counter reuse, forward jumps outside the reviewed window and half-range ambiguity end reconciliation. Outstanding values become **uncertain across ambiguity**. A later advancing baseline anchors a new review segment without inferring gaps across that boundary. These segments are analyst boundaries, not claims of physical resets. Rejected and idle records cannot anchor or fill a stream, and APIDs remain independent.

Full JSON/HTML reports, strict CLI imports and immutable history include this derived review ledger under the run hash. Existing CSV record decisions remain the original record-level evidence. This restricted educational parser is not a flight or operational ground system, and has no mandatory packet payload checksum or sender authentication.
