
class QueryResults:

    def __init__(self, rows, formatter=None):
        self.rows = rows
        self.formatter = formatter  # in case you want to use format_results

    @property
    def raw(self):
        return self.rows

    @property
    def dicts(self):
        if not self.rows:
            return []

        results = []
        for row in self.rows:
            d = {}
            for k, v in dict(row).items():
                if isinstance(v, bytes):
                    try:
                        v = v.decode("utf-8")
                    except:
                        v = str(v)  # secured fallback
                d[k] = v
            results.append(d)
        return results


    @property
    def json(self):
        import json
        return json.loads(json.dumps(self.dicts, indent=4, ensure_ascii=False))

    @property
    def table(self):
        if self.formatter:
            return self.formatter(self.rows)

        # simple table as default
        if not self.rows:
            return "No results."

        headers = self.rows[0].keys()
        out = " | ".join(headers) + "\n"
        out += "-" * len(out) + "\n"

        for row in self.rows:
            out += " | ".join(str(row[h]) for h in headers) + "\n"

        return out

    @property
    def first(self):
        return self.dicts[0] if self.rows else None

    @property
    def scalar(self):
        return list(self.rows[0].values())[0] if self.rows else None

    @property
    def count(self):
        return len(self.rows)