# Copyright (C) 2023 Anthony Harrison
# SPDX-License-Identifier: Apache-2.0

import html

from lib4sbom.output import SBOMOutput

from sbom2doc.docbuilder.docbuilder import DocBuilder


class HTMLBuilder(DocBuilder):
    def __init__(self, style=None):
        self.html_document = []

    def _sanitise(self, item):
        return html.escape(str(item), quote=True)

    def heading(self, level, title, number=True):
        self.html_document.append(f"\n<h{level}>{self._sanitise(title)}</h{level}>\n")

    def paragraph(self, text, safecontent=False):
        # Trusted sources are not sanitised
        if safecontent:
            self.html_document.append(f"<p>{text}</p>")
        else:
            self.html_document.append(f"<p>{self._sanitise(text)}</p>")

    def createtable(self, header, validate=None):
        # Layout is [headings, ....]
        self.html_document.append(
            "<table class='table table-striped table-bordered'>\n"
        )

        # table_headings = " | ".join(h for h in header)

        self.html_document.append("<thead><tr>\n")
        for d in header:
            self.html_document.append(f"<th scope='col'>{self._sanitise(d)}</th>\n")
        self.html_document.append("</tr>\n")
        self.html_document.append("</thead><tbody class='table-group-divider'>\n")

    def addrow(self, data):
        # Add row to table
        my_data = []
        for d in data:
            if d is not None:
                my_data.append(d)
            else:
                my_data.append("")
        # table_row = " | ".join(d for d in my_data)
        self.html_document.append("<tr>\n")
        for d in my_data:
            self.html_document.append(f"<td>{self._sanitise(d)}</td>\n")
        self.html_document.append("</tr>\n")

    def showtable(self, widths=None):
        self.html_document.append("</tbody></table>\n")

    def publish(self, filename):
        html_doc = SBOMOutput(filename=filename)
        html_doc.generate_output(self.html_document)
