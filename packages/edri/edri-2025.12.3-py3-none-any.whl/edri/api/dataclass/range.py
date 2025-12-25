from dataclasses import dataclass


@dataclass(slots=True)
class RangeSpec:
    first: int | None = None
    last: int | None = None
    suffix_length: int | None = None


@dataclass(slots=True)
class RangeValue:
    unit: str
    specs: tuple[RangeSpec, ...]

    def content_range(
        self,
        full_length: int | None,
        start: int,
        end: int,
    ) -> str:
        """
        Build Content-Range for a *single* range response (206).

        Args:
          full_length: total representation length, or None if unknown.
          start, end: inclusive byte positions of the payload actually served.
        Returns:
          e.g. "bytes 0-99/1234" or "bytes 0-99/*"
        """
        if self.unit != "bytes":
            raise ValueError(f"Content-Range generation not implemented for unit={self.unit!r}")

        if start < 0 or end < start:
            raise ValueError("Invalid start/end")

        if full_length is not None:
            if full_length < 0:
                raise ValueError("full_length must be >= 0")
            # When length known, served range must be within it (end inclusive)
            if full_length == 0:
                raise ValueError("Cannot serve a non-empty range for full_length=0")
            if end >= full_length:
                raise ValueError("end must be < full_length when full_length is known")

            return f"bytes {start}-{end}/{full_length}"

        return f"bytes {start}-{end}/*"

    @staticmethod
    def content_range_unsatisfied(*, unit: str = "bytes", full_length: int) -> str:
        """
        Build Content-Range for 416 Range Not Satisfiable.

        Returns:
          e.g. "bytes */1234"
        """
        if full_length < 0:
            raise ValueError("full_length must be >= 0")
        return f"{unit} */{full_length}"


    def content_length(self, start: int, end: int) -> int:
        """
        Content-Length for a *single* resolved range body (206).
        """
        if self.unit != "bytes":
            raise ValueError(f"Content-Length not implemented for unit={self.unit!r}")
        if start < 0 or end < start:
            raise ValueError("Invalid start/end")
        return (end - start) + 1