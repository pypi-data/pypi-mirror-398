from typing import Dict, Optional
from dataclasses import dataclass, field

@dataclass
class Schedule:
    
    # Timer/schedule fields
    ts_raw: Dict[str, int] = field(default_factory=dict)   # raw int values
    ts_decoded: Dict[str, Dict[str, Optional[str]]] = field(default_factory=dict)  
    # Each entry: { "from": "HH:MM", "to": "HH:MM", "days": "Mon,Tue", "mode": "Boost" }  
       
    shrs_raw: Optional[int] = None
    silent_hours_decoded: Dict[str, Optional[str]] = field(default_factory=dict)      
    
    DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    MODE_MAP = {
        0b001: "Normal",
        0b010: "Low",
        0b011: "Boost",
        0b100: "Purge",
    }   
        
    def minutes_to_hhmm(self, mins: int) -> str:
        """Convert minute count to HH:MM (wraps at 24h)."""
        # mins = mins % (24 * 60)
        h = mins // 60
        m = mins % 60
        return f"{h:02d}:{m:02d}"    
    
    def hhmm_to_minutes(self, hhmm: str) -> int:
        """Convert HH:MM string to total minutes."""
        h, m = map(int, hhmm.split(":"))
        return h * 60 + m
    
    

    def decode_ts_field(self, ts_name: str, ts_val: int, is_ts: bool = True) -> None:
        """Decode a tsN field and update state_obj.ts_raw and state_obj.ts_decoded."""
        # Save raw value
        decoded: Dict[str, Optional[str]]        
        
        if is_ts:
            self.ts_raw[ts_name] = ts_val
            decoded = self.ts_decoded.setdefault(ts_name, {})
        else:
            self.shrs_raw = ts_val
            decoded = self.silent_hours_decoded or {}
            self.silent_hours_decoded = decoded


        # Ensure 32-bit view
        bin32 = format(ts_val & 0xFFFFFFFF, '032b')

        # Slice groups: days (0:7), time_to (7:18), time_from (18:29), mode (29:32)
        days_bits_s  = bin32[0:7]
        time_to_s    = bin32[7:18]
        time_from_s  = bin32[18:29]
        mode_s       = bin32[29:32]

        days_bits = int(days_bits_s, 2)
        time_to_val = int(time_to_s, 2)
        time_from_val = int(time_from_s, 2)
        mode_bits = int(mode_s, 2)

        # Convert times
        time_from = self.minutes_to_hhmm(time_from_val)
        time_to   = self.minutes_to_hhmm(time_to_val)

        # Days decode
        if days_bits == 0b1111111:
            days_str = "Every day"
        else:
            days = [self.DAY_NAMES[i] for i in range(7) if (days_bits >> i) & 1]
            days_str = ",".join(days) if days else "None"

        # Mode decode
        mode_str = self.MODE_MAP.get(mode_bits, f"Unknown({mode_bits:#03b})")

        decoded["from"] = time_from
        decoded["to"] = time_to
        decoded["days"] = days_str
        decoded["mode"] = mode_str
        
        
    def encode_ts_field(self, decoded: dict) -> int:
        """Encode a decoded dict back into a 32-bit ts_val integer.
            Layout (as used by decode_ts_field):
            bits 31..25 : days (7 bits)
            bits 24..14 : time_to (11 bits)
            bits 13..3  : time_from (11 bits)
            bits 2..0   : mode (3 bits)
            decoded keys: "from", "to", "days", "mode" (values may be None) """
        # Convert times
        time_from_val = self.hhmm_to_minutes(decoded.get("from", "00:00"))
        time_to_val   = self.hhmm_to_minutes(decoded.get("to", "00:00"))

        # Days encode
        days_str = decoded.get("days", "None")
        if days_str == "Every day":
            days_bits = 0b1111111
        elif days_str == "None":
            days_bits = 0
        else:
            days_bits = 0
            for day in days_str.split(","):
                day = day.strip()
                if day in self.DAY_NAMES:
                    i = self.DAY_NAMES.index(day)
                    days_bits |= (1 << (6 - i))  # reverse mapping

        # Mode encode
        mode_str = decoded.get("mode", "Normal")
        # Try to reverse lookup in MODE_MAP
        mode_bits = None
        for k, v in self.MODE_MAP.items():
            if v == mode_str:
                mode_bits = k
                break
        if mode_bits is None:
            # fallback: parse Unknown(xxx)
            import re
            m = re.match(r"Unknown\(0b([01]{3})\)", mode_str)
            mode_bits = int(m.group(1), 2) if m else 0

        # Combine into 32-bit integer
        ts_val = (
            (days_bits   << 25) |  # bits 31..25
            (time_to_val << 14) |  # bits 24..14
            (time_from_val << 3) | # bits 13..3
            (mode_bits)            # bits 2..0
        ) & 0xFFFFFFFF  # ensure 32-bit
        return ts_val


 