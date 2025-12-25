from typing import Optional


class _chunk:
    def __init__(self, cap=16) -> None:
        self.buffer: list[Optional[str]] = [None] * cap
        self.count = 0
        self.next: Optional[_chunk] = None


class stringbuilder:
    def __init__(self, chunk_cap=16) -> None:
        self.__chunk_cap = chunk_cap
        self.__head = _chunk(self.__chunk_cap)
        self.__tail = self.__head

    def append(self, arg: object) -> None:
        for c in str(arg):
            if self.__tail.count >= self.__chunk_cap:
                new_chunk = _chunk(self.__chunk_cap)
                self.__tail.next = new_chunk
                self.__tail = new_chunk
            self.__tail.buffer[self.__tail.count] = c
            self.__tail.count += 1

    def append_format(self, fmt: str, *args: object) -> None:
        self.append(fmt.format(*args))

    def append_join(self, sep: str, *args: object) -> None:
        self.append(sep.join(str(a) for a in args))

    def append_line(self, arg: object) -> None:
        last_char = ""
        if self.__tail.count > 0:
            last_char = self.__tail.buffer[-1]

        is_empty = self.__head.count == 0 and self.__head.next is None
        if not is_empty and last_char != "\n":
            self.append("\n")

        self.append(arg)

    def insert(self, idx: int, arg: object) -> None:
        if not arg:
            return

        current_chunk = self.__head
        remaining_idx = idx
        while current_chunk:
            if remaining_idx <= current_chunk.count:
                break
            remaining_idx -= current_chunk.count
            current_chunk = current_chunk.next
        else:
            self.append(arg)
            return

        tail_buffer = []
        temp_chunk = current_chunk
        tail_buffer.extend(temp_chunk.buffer[remaining_idx : temp_chunk.count])
        temp_chunk = temp_chunk.next
        while temp_chunk:
            tail_buffer.extend(temp_chunk.buffer[: temp_chunk.count])
            temp_chunk = temp_chunk.next

        current_chunk.count = remaining_idx
        current_chunk.next = None
        self.__tail = current_chunk

        self.append(arg)
        for item in tail_buffer:
            if item is not None:
                self.append(item)

    def remove(self, idx: int, length: int) -> None:
        if length <= 0:
            return

        current_str = str(self)
        if idx < 0 or idx > len(current_str):
            return

        new_str = current_str[:idx] + current_str[idx + length :]

        self.clear()
        self.append(new_str)

    def clear(self) -> None:
        self.__head = _chunk(self.__chunk_cap)
        self.__tail = self.__head

    def __str__(self) -> str:
        result = []
        cur = self.__head
        while cur:
            result.extend(cur.buffer[: cur.count])
            cur = cur.next
        return "".join(char for char in result if char is not None)

    def __repr__(self) -> str:
        length = len(text := str(self))
        preview = text if length <= 50 else text[:47] + "..."
        return f"<{self.__class__.__name__} length={length} value={repr(preview)}>"
