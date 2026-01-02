from __future__ import annotations

import os
import pprint
import re
import shutil
import sys
from collections import defaultdict

import yaml
from snakemd import Document, Inline, MDList, Table

from skoufas_dbf_reader.correction_data import plain_author_re
from skoufas_dbf_reader.field_extractors import (
    author_corrections,
    authors_from_a01,
    copies_from_a17_a18_a30,
    curator_from_a16,
    dewey_from_a04_a05,
    donation_from_a17_a30,
    edition_from_a07,
    edition_year_from_a09_a10,
    editor_from_a08_a09,
    entry_numbers_from_a04_a05_a06_a07_a08_a18_a19,
    has_cd_from_a02_a03_a12_a13_a14_a17_a18_a22_a30,
    has_dvd_from_a30,
    isbn_from_a17_a18_a19_a22_a30,
    language_from_a01_a02,
    material_from_a18_a30,
    none_if_empty_or_stripped,
    notes_from_a17_a18_a21_a30,
    offprint_from_a17_a21_a30,
    pages_from_a11,
    subtitle_from_a03,
    title_from_a02,
    topics_from_a12_to_a15_a20_a22_to_a24,
    translator_from_a06,
    volume_from_a17_a18_a20_a30,
)
from skoufas_dbf_reader.utilities import (
    all_entries,
    check_ean,
    check_isbn,
    check_issn,
    is_valid_dewey_strict,
    romanize,
)


def report_single_fields(reports_directory: str):
    field_values: list[set[str]] = [set() for _ in range(31)]
    os.makedirs(os.path.join(reports_directory, "single-field"), exist_ok=True)
    for entry in all_entries():
        for i in range(1, 31):
            if i in entry and entry[i] and entry[i].strip():
                field_values[i].add(entry[i].strip())
    for i in range(1, 31):
        doc = Document()
        doc.add_heading(f"Τιμές στη θέση {i:02}")
        doc.add_unordered_list([f"`{v}`" for v in sorted(field_values[i])])
        with open(
            os.path.join(reports_directory, "single-field", f"field_{i:02}.md"), "w", encoding="utf-8"
        ) as outfile:
            outfile.write(str(doc))

    doc = Document()
    doc.add_heading("Τιμές στις στήλες των καρτελών")
    doc.add_unordered_list([str(Inline(f"Στήλη {i}", link=f"./field_{i:02}.html")) for i in range(1, 31)])
    with open(os.path.join(reports_directory, "single-field", "index.md"), "w", encoding="utf-8") as outfile:
        outfile.write(str(doc))


def report_single_extracted_fields(reports_directory: str):
    field_values: defaultdict[str, list[str | list[str]]] = defaultdict(list)
    for entry in all_entries():
        authors = authors_from_a01(entry[1])
        for author in authors:
            field_values["author"].append(author)
            if plain_author_re.fullmatch(author) or author in author_corrections().values():
                field_values["plain_author"].append(author)
            else:
                field_values["weird_author"].append(author)

        language = language_from_a01_a02(entry[1], entry[2])
        if language:
            field_values["language"].append(language)

        title = title_from_a02(entry[2])
        if title:
            field_values["title"].append(title)

        subtitle = subtitle_from_a03(entry[3])
        if subtitle:
            field_values["subtitle"].append(subtitle)

        dewey = dewey_from_a04_a05(entry[4], entry[5])
        if dewey:
            field_values["dewey"].append(dewey)

        entry_numbers = entry_numbers_from_a04_a05_a06_a07_a08_a18_a19(
            entry[4], entry[5], entry[6], entry[7], entry[8], entry[18], entry[19]
        )

        field_values["entry_number_lists"].append(entry_numbers)
        for entry_number in entry_numbers:
            field_values["entry_numbers"].append(entry_number)

        translator = translator_from_a06(entry[6])
        if translator:
            translators = translator.split("!!")
            for single_translator in translators:
                field_values["translator"].append(single_translator)
                translator_surname_name = single_translator.split(",", maxsplit=1)
                if len(translator_surname_name) == 2:
                    field_values["translator_family_name"].append(translator_surname_name[0])
                    if translator_surname_name[1].endswith("."):
                        field_values["translator_name_abbreviations"].append(translator_surname_name[1])
                    else:
                        field_values["translator_names"].append(translator_surname_name[1])

        edition = edition_from_a07(entry[7])
        if edition:
            field_values["edition"].append(edition)

        editor = editor_from_a08_a09(entry[8], entry[9])
        if editor:
            if not editor[0] or not editor[1]:
                field_values["editor"].append(f"{editor[0]} // {editor[1]} ({entry[0]})")
            else:
                field_values["editor"].append(f"{editor[0]} // {editor[1]}")

        edition_year = edition_year_from_a09_a10(entry[9], entry[10])
        if edition_year:
            field_values["edition_year"].append(str(edition_year))

        pages = pages_from_a11(entry[11])
        if pages:
            field_values["pages"].append(str(pages))

        topic_list = topics_from_a12_to_a15_a20_a22_to_a24(
            [
                entry[12],
                entry[13],
                entry[14],
                entry[15],
                entry[20],
                entry[22],
                entry[23],
                entry[24],
            ]
        )
        field_values["topic_lists"].append(topic_list)
        for topic in topic_list:
            field_values["topics"].append(topic)

        curator = curator_from_a16(entry[16])
        if curator:
            field_values["curator"].append(curator)

        copies = copies_from_a17_a18_a30(entry[17], entry[18], entry[30])
        if copies:
            field_values["copies"].append(str(copies))

        donation = donation_from_a17_a30(entry[17], entry[30])
        if donation:
            field_values["donation"].append(donation)

        volume = volume_from_a17_a18_a20_a30(entry[17], entry[18], entry[20], entry[30])
        if volume:
            field_values["volume"].append(volume)

        material = material_from_a18_a30(entry[18], entry[30])
        if material:
            field_values["material"].append(material)

        notes = notes_from_a17_a18_a21_a30(entry[17], entry[18], entry[21], entry[30])
        if notes:
            field_values["notes"].append(notes)

        isbn: str | None = isbn_from_a17_a18_a19_a22_a30(entry[17], entry[18], entry[19], entry[22], entry[30])
        if isbn:
            if not check_isbn(isbn):
                field_values["isbn"].append(isbn)
            if not check_issn(isbn):
                field_values["issn"].append(isbn)
            if not check_ean(isbn):
                field_values["ean"].append(isbn)

    os.makedirs(os.path.join(reports_directory, "calculated-field"), exist_ok=True)

    index = Document()
    index.add_heading("Υπολογισμένες Τιμές")
    links: list[str] = []

    for k, values in field_values.items():
        values = [pprint.pformat(value) for value in values]
        with open(
            os.path.join(reports_directory, "calculated-field", f"calculated_field_{k}.md"), "w", encoding="utf-8"
        ) as outfile:
            doc = Document()
            doc.add_heading(f"Υπολογισμένες τιμές για την ιδιότητα {k}, αλφαβητικά")
            doc.add_unordered_list([f"`{v}`" for v in sorted(set(values))])
            outfile.write(str(doc))
            links.append(
                str(
                    Inline(f"Υπολογισμένες τιμές για την ιδιότητα {k}, αλφαβητικά", link=f"./calculated_field_{k}.html")
                )
            )
        with open(
            os.path.join(reports_directory, "calculated-field", f"calculated_field_{k}_romanize_sort.md"),
            "w",
            encoding="utf-8",
        ) as outfile:
            doc = Document()
            doc.add_heading(f"Υπολογισμένες τιμές για την ιδιότητα {k}, φωνητικά")
            doc.add_unordered_list([f"`{v}` # *{romanize(v)}*" for v in sorted(set(values), key=romanize)])
            outfile.write(str(doc))
            links.append(
                str(
                    Inline(
                        f"Υπολογισμένες τιμές για την ιδιότητα {k}, φωνητικά",
                        link=f"./calculated_field_{k}_romanize_sort.html",
                    )
                )
            )
    index.add_unordered_list(links)
    with open(os.path.join(reports_directory, "calculated-field", "index.md"), "w", encoding="utf-8") as outfile:
        outfile.write(str(index))


def report_invalid_dewey(reports_directory: str):
    invalid_output_dewey: defaultdict[str, list[str]] = defaultdict(list)
    no_output_dewey: defaultdict[str, list[str]] = defaultdict(list)
    for entry in all_entries():
        dewey = dewey_from_a04_a05(entry[4], entry[5])
        if dewey:
            if not is_valid_dewey_strict(dewey):
                invalid_output_dewey[dewey].append(str(entry[0]))
        else:
            if none_if_empty_or_stripped(entry[4]):
                no_output_dewey[entry[4]].append(str(entry[0]))

    os.makedirs(os.path.join(reports_directory, "checks"), exist_ok=True)
    with open(os.path.join(reports_directory, "checks", "invalid_dewey.md"), "w", encoding="utf-8") as outfile:
        doc = Document()
        doc.add_heading("Dewey με προβληματικές τιμές στην έξοδο")
        for k, v in sorted(invalid_output_dewey.items()):
            doc.add_heading(k, level=2)
            doc.add_unordered_list([str(Inline(entry, link=f"../entries/entry_{entry:05}.html")) for entry in v])
        doc.add_heading("Dewey στην είσοδο που δεν βγαίνουν στην έξοδο")
        for k, v in sorted(no_output_dewey.items()):
            doc.add_heading(k, level=2)
            doc.add_unordered_list([str(Inline(entry, link=f"../entries/entry_{entry:05}.html")) for entry in v])
        outfile.write(str(doc))


def report_weird_names(reports_directory: str):
    os.makedirs(os.path.join(reports_directory, "checks"), exist_ok=True)
    weird_translators: list[str] = []
    weird_authors: list[str] = []
    weird_curators: list[str] = []
    weird_donors: list[str] = []
    valid_name_re = re.compile(r"[A-ZΑ-Ω\-]+,[A-ZΑ-Ω\.]*\.?")
    valid_name2_re = re.compile(r"[A-ZΑ-Ω\-]+,[A-ZΑ-Ω\.]*,[A-ZΑ-Ω\.]*\.?")
    valid_name3_re = re.compile(r"[A-ZΑ-Ω\-]+,[A-ZΑ-Ω\.]*\.?@[A-ZΑ-Ω\-]+")
    valid_name4_re = re.compile(r"[A-ZΑ-Ω\-]+,[A-ZΑ-Ω\.]*,[A-ZΑ-Ω\.]*\.?@[A-ZΑ-Ω\-]+")
    for entry in all_entries():
        translator = translator_from_a06(entry[6])
        if translator:
            translators = translator.split("!!")
            for translator in translators:
                if not valid_name_re.fullmatch(translator):
                    weird_translators.append(translator)
        authors = authors_from_a01(entry[1])
        for author in authors:
            if (
                (not valid_name_re.fullmatch(author))
                and (not valid_name2_re.fullmatch(author))
                and (not valid_name3_re.fullmatch(author))
                and (not valid_name4_re.fullmatch(author))
            ):
                weird_authors.append(author)
        curator = curator_from_a16(entry[16])
        if curator:
            curators = curator.split("!!")
            for curator in curators:
                if not valid_name_re.fullmatch(curator):
                    weird_curators.append(curator)
        donor = donation_from_a17_a30(entry[17], entry[30])
        if donor:
            donors = donor.split("!!")
            for donor in donors:
                if not valid_name_re.fullmatch(donor):
                    weird_donors.append(donor)

    for field, greek_name, thelist in [
        ("translators", "Μεταφραστές", weird_translators),
        ("authors", "Συγγραφείς", weird_authors),
        ("curators", "Επιμελητές", weird_curators),
        ("donors", "Δωρητές", weird_donors),
    ]:
        with open(os.path.join(reports_directory, "checks", f"invalid_{field}.md"), "w", encoding="utf-8") as outfile:
            doc = Document()
            doc.add_heading(f"{greek_name} με παράξενα ονόματα")
            doc.add_unordered_list(sorted(set(thelist)))
            outfile.write(str(doc))


def report_donors(reports_directory: str):
    os.makedirs(os.path.join(reports_directory, "checks"), exist_ok=True)
    count_map: defaultdict[str, int] = defaultdict(int)
    for entry in all_entries():
        donors = donation_from_a17_a30(entry[17], entry[30])
        if donors:
            for donor in donors.split("!!"):
                count_map[donor] = count_map[donor] + 1
    donor_count_list: list[list[str]] = []
    for donor, count in sorted(count_map.items(), reverse=True, key=lambda x: x[1]):
        donor_count_list.append([donor, str(count)])

    with open(os.path.join(reports_directory, "checks", "donors.md"), "w", encoding="utf-8") as outfile:
        doc = Document()
        doc.add_heading("Δωρητές")
        doc.add_table(["Δωρητής", "Αριθμός βιβλίων"], donor_count_list)
        outfile.write(str(doc))


def report_isbns(reports_directory: str):
    doc = Document()
    doc.add_heading("Προβληματικά ISBN")
    doc.add_table_of_contents()

    for entry in all_entries():
        result = isbn_from_a17_a18_a19_a22_a30(
            entry[17],
            entry[18],
            entry[19],
            entry[22],
            entry[30],
        )
        if not result:
            continue
        checks = [check_isbn(result), check_issn(result), check_ean(result)]
        if None in checks:
            continue

        doc.add_heading(result, level=2)
        doc.add_unordered_list([check for check in checks if check])

        doc.add_heading("Αρχική Καρτέλα στο DBASE", level=3)
        doc.add_code(code=entry_as_yaml(entry, minimal=True), lang="yaml")

    with open(os.path.join(reports_directory, "checks", "invalid_isbn.md"), "w", encoding="utf-8") as outfile:
        outfile.write(str(doc))


def report_entry_numbers(reports_directory: str):
    all_entry_numbers: dict[str, dict[int, str]] = {}

    no_entry_numbers = Document()
    no_entry_numbers.add_heading("Καρτέλες χωρίς αριθμό εισαγωγής")

    non_numeric = Document()
    non_numeric.add_heading("Καρτέλες με μή αριθμητικό αριθμό εισαγωγής")

    duplicate_entry_numbers: defaultdict[str, list[dict[int, str]]] = defaultdict(list)

    for entry in all_entries():
        entry_numbers = entry_numbers_from_a04_a05_a06_a07_a08_a18_a19(
            entry[4], entry[5], entry[6], entry[7], entry[8], entry[18], entry[19]
        )
        if not entry_numbers:
            no_entry_numbers.add_horizontal_rule()
            no_entry_numbers.add_code(entry_as_yaml(entry, minimal=True), lang="yaml")
        else:
            for n in entry_numbers:
                if n in all_entry_numbers:
                    if not duplicate_entry_numbers[n]:
                        duplicate_entry_numbers[n].append(all_entry_numbers[n])
                    duplicate_entry_numbers[n].append(entry)
                else:
                    all_entry_numbers[n] = entry
                if not n.isnumeric():
                    non_numeric.add_horizontal_rule()
                    non_numeric.add_paragraph(n)
                    non_numeric.add_code(entry_as_yaml(entry, minimal=True), lang="yaml")

    os.makedirs(os.path.join(reports_directory, "checks"), exist_ok=True)
    with open(os.path.join(reports_directory, "checks", "no_entry_numbers.md"), "w", encoding="utf-8") as outfile:
        outfile.write(str(no_entry_numbers))
    with open(
        os.path.join(reports_directory, "checks", "non_numeric_entry_numbers.md"), "w", encoding="utf-8"
    ) as outfile:
        outfile.write(str(non_numeric))

    with open(
        os.path.join(reports_directory, "checks", "duplicate_entry_numbers.md"), "w", encoding="utf-8"
    ) as outfile:
        dup = Document()
        dup.add_heading("Καρτέλες με διπλοπερασμένο αριθμητικό αριθμό εισαγωγής")
        for entry_number, entries in duplicate_entry_numbers.items():
            dup.add_horizontal_rule()
            dup.add_paragraph(entry_number)
            for entry in entries:
                dup.add_code(entry_as_yaml(entry, minimal=True), lang="yaml")
        outfile.write(str(dup))


def entry_as_yaml(entry: dict[int, str], minimal: bool) -> str:
    """return an entry for a code section"""
    if minimal:
        minimal_entry = {k: v for k, v in entry.items() if v}
        return yaml.dump(minimal_entry, default_flow_style=False, allow_unicode=True)
    return yaml.dump(entry, default_flow_style=False, allow_unicode=True)


def report_entries(reports_directory: str):
    os.makedirs(os.path.join(reports_directory, "entries"), exist_ok=True)
    all_id_titles: list[tuple[str, str]] = []
    by_author: defaultdict[str, defaultdict[str, list[tuple[str, str]]]] = defaultdict(lambda: defaultdict(list))
    by_dewey: defaultdict[str, list[tuple[str, str]]] = defaultdict(list)

    for entry in all_entries():
        translator = translator_from_a06(entry[6])
        translators: list[str] = []
        if translator:
            for single_translator in translator.split("!!"):
                translator_surname_name = single_translator.split(",", maxsplit=1)
                if len(translator_surname_name) == 2:
                    if translator_surname_name[1].endswith("."):
                        translators.append(
                            f"Επίθετο:{translator_surname_name[0]}, Μή πλήρες όνομα: {translator_surname_name[1]}"
                        )
                    else:
                        translators.append(f"Επίθετο:{translator_surname_name[0]}, Oνομα: {translator_surname_name[1]}")
                else:
                    translators.append(f"{single_translator}")

        donation = donation_from_a17_a30(entry[17], entry[30])
        donors: list[str] = []
        if donation:
            donors = donation.split("!!")

        editor = editor_from_a08_a09(entry[8], entry[9])
        if editor:
            editor = f"{editor[0]} ({editor[1]})"

        topic_list = topics_from_a12_to_a15_a20_a22_to_a24(
            [
                entry[12],
                entry[13],
                entry[14],
                entry[15],
                entry[20],
                entry[22],
                entry[23],
                entry[24],
            ]
        )

        isbn_issn_ean = isbn_from_a17_a18_a19_a22_a30(entry[17], entry[18], entry[19], entry[22], entry[30])
        isbn = ""
        issn = ""
        ean = ""
        if isbn_issn_ean:
            if not check_isbn(isbn_issn_ean):
                isbn = isbn_issn_ean
            if not check_issn(isbn_issn_ean):
                issn = isbn_issn_ean
            if not check_ean(isbn_issn_ean):
                ean = isbn_issn_ean

        doc = Document()

        doc.add_heading("Τίτλος")
        doc.add_paragraph(str(title_from_a02(entry[2])))
        doc.add_paragraph(str(subtitle_from_a03(entry[3])))
        doc.add_paragraph(
            str(
                Inline(
                    text="Στο library.skoufas.gr", link=f"https://library.skoufas.gr/books/by-entry-number/{entry[0]}"
                )
            )
        )

        doc.add_heading("Συγγραφείς", level=2)
        doc.add_unordered_list(authors_from_a01(entry[1]))

        doc.add_heading("Αριθμοί Εισαγωγης", level=2)
        doc.add_unordered_list(
            entry_numbers_from_a04_a05_a06_a07_a08_a18_a19(
                entry[4], entry[5], entry[6], entry[7], entry[8], entry[18], entry[19]
            )
        )

        doc.add_table(
            ["Πεδίο", "Τιμή"],
            [
                ["dbase_number", str(entry[0])],
                ["Γλώσσα", str(language_from_a01_a02(entry[1], entry[2]))],
                ["Dewey", str(dewey_from_a04_a05(entry[4], entry[5]))],
                ["Έκδοση", str(edition_from_a07(entry[7]))],
                ["Εκδότης (Πόλη)", f"{editor}"],
                ["Χρόνος έκδοσης", f"{edition_year_from_a09_a10(entry[9], entry[10])}"],
                ["Σελίδες", f"{pages_from_a11(entry[11])}"],
                ["Επιμελητής", f"{curator_from_a16(entry[16])}"],
                ["Αντίτυπα", f"{copies_from_a17_a18_a30(entry[17], entry[18], entry[30])}"],
                ["Δωρητές", str(MDList(donors))],
                ["Τεύχος/Τόμος", f"{volume_from_a17_a18_a20_a30(entry[17], entry[18], entry[20], entry[30])}"],
                ["Υλικό", f"{material_from_a18_a30(entry[18], entry[30])}"],
                ["Σημειώσεις", f"{notes_from_a17_a18_a21_a30(entry[17], entry[18], entry[21], entry[30])}"],
                ["ISBN", isbn],
                ["ISSN", issn],
                ["EAN", ean],
            ],
            [Table.Align.LEFT, Table.Align.RIGHT],
            0,
        )

        doc.add_paragraph("Μεταφραστές")
        doc.add_unordered_list(translators)

        doc.add_paragraph("Θέματα")
        doc.add_unordered_list(topic_list)

        doc.add_paragraph("Ιδιότητες")
        doc.add_block(
            MDList(
                ["Εχει CD"],
                checked=has_cd_from_a02_a03_a12_a13_a14_a17_a18_a22_a30(
                    [
                        entry[2],
                        entry[3],
                        entry[12],
                        entry[13],
                        entry[14],
                        entry[17],
                        entry[18],
                        entry[22],
                        entry[30],
                    ]
                ),
            )
        )

        doc.add_block(
            MDList(
                ["Εχει DVD"],
                checked=has_dvd_from_a30(
                    [
                        entry[30],
                    ]
                ),
            )
        )

        doc.add_block(MDList(["Ανάτυπο"], checked=offprint_from_a17_a21_a30(entry[17], entry[21], entry[30])))

        doc.add_heading("Αρχική Καρτέλα στο DBASE", level=1)
        doc.add_code(code=entry_as_yaml(entry, minimal=False), lang="yaml")

        title = title_from_a02(entry[2])
        if not title:
            title = "Χωρίς Τίτλο"
        subtitle = subtitle_from_a03(entry[3])
        if subtitle:
            title += " - " + subtitle

        all_id_titles.append((entry[0], title))
        for author in authors_from_a01(entry[1]):
            if len(author) == 0:
                by_author["#"]["Χωρίς συγγραφέα"].append((entry[0], title))
            else:
                by_author[author[0]][author].append((entry[0], title))

        dewey = dewey_from_a04_a05(entry[4], entry[5])

        if dewey:
            by_dewey[dewey].append((entry[0], title))
        else:
            by_dewey["Xωρίς dewey"].append((entry[0], title))

        with open(
            os.path.join(reports_directory, "entries", f"entry_{entry[0]:05}.md"), "w", encoding="utf-8"
        ) as outfile:
            outfile.write(str(doc))

    index = Document()
    index.add_heading("Όλες οι καρτέλες")
    index.add_table_of_contents(range(1, 3))

    def divide_chunks(inlist: list[tuple[str, str]], size: int):
        for i in range(0, len(inlist), size):
            yield inlist[i : i + size]

    all_divided = list(divide_chunks(all_id_titles, 1000))
    for thousands, sublist in enumerate(all_divided):
        index.add_heading(f"Απο {thousands * 1000} ως {thousands * 1000 + len(sublist)}")
        sublist = [str(Inline(f"{int(id):05}: {title}", link=f"./entry_{int(id):05}.html")) for id, title in sublist]
        index.add_unordered_list(sublist)

    with open(os.path.join(reports_directory, "entries", "index.md"), "w", encoding="utf-8") as outfile:
        outfile.write(str(index))

    index_by_author = Document()
    index_by_author.add_heading("Όλες οι καρτέλες, κατα συγγραφέα")
    index_by_author.add_table_of_contents(range(1, 3))
    for author_initial, author_dict in sorted(by_author.items()):
        index_by_author.add_heading(author_initial, level=2)
        for author, entry_list in sorted(author_dict.items()):
            index_by_author.add_heading(author, level=3)
            entry_list = [
                str(Inline(f"{int(id):05}: {title}", link=f"./entry_{int(id):05}.html")) for id, title in entry_list
            ]
            index_by_author.add_unordered_list(entry_list)
    with open(os.path.join(reports_directory, "entries", "index_by_author.md"), "w", encoding="utf-8") as outfile:
        outfile.write(str(index_by_author))

    index_by_dewey = Document()
    index_by_dewey.add_heading("Όλες οι καρτέλες, κατα συγγραφέα")
    index_by_dewey.add_table_of_contents(range(1, 3))
    for dewey, entry_list in sorted(by_dewey.items()):
        index_by_dewey.add_heading(dewey, level=2)
        entry_list = [
            str(Inline(f"{int(id):05}: {title}", link=f"./entry_{int(id):05}.html")) for id, title in entry_list
        ]
        index_by_dewey.add_unordered_list(entry_list)
    with open(os.path.join(reports_directory, "entries", "index_by_dewey.md"), "w", encoding="utf-8") as outfile:
        outfile.write(str(index_by_dewey))


def add_index(reports_directory: str):
    os.makedirs(reports_directory, exist_ok=True)
    doc = Document()

    doc.add_heading("Βιβλιοθήκη Σκουφά: προσωρινός κατάλογος βιβλίων")
    doc.add_table_of_contents()

    doc.add_paragraph(str(Inline("Όλες οι καρτέλες", link="./entries/index.html")))
    doc.add_paragraph(str(Inline("Όλες οι καρτέλες, κατα συγγραφέα", link="./entries/index_by_author.html")))
    doc.add_paragraph(str(Inline("Όλες οι καρτέλες, κατα dewey", link="./entries/index_by_dewey.html")))

    doc.add_heading("Τιμές κατα στήλη")
    doc.add_paragraph(str(Inline("Υπολογισμένες τιμές", link="./calculated-field/index.html")))
    doc.add_paragraph(str(Inline("Τιμές στις στήλες των καρτελών", link="./single-field/index.html")))

    doc.add_heading("Ελεγκτικές Αναφορές")
    doc.add_paragraph(
        str(
            Inline(
                "Καρτέλες με διπλοπερασμένο αριθμητικό αριθμό εισαγωγής", link="./checks/duplicate_entry_numbers.html"
            )
        )
    )
    doc.add_paragraph(str(Inline("Καρτέλες χωρίς αριθμό εισαγωγής", link="./checks/no_entry_numbers.html")))
    doc.add_paragraph(
        str(Inline("Καρτέλες με μή αριθμητικό αριθμό εισαγωγής", link="./checks/non_numeric_entry_numbers.html"))
    )
    doc.add_paragraph(str(Inline("Dewey με προβληματικές τιμές", link="./checks/invalid_dewey.html")))

    doc.add_paragraph(str(Inline("Μεταφραστές με παράξενα ονόματα", link="./checks/invalid_translators.html")))
    doc.add_paragraph(str(Inline("Συγγραφείς με παράξενα ονόματα", link="./checks/invalid_authors.html")))
    doc.add_paragraph(str(Inline("Επιμελητές με παράξενα ονόματα", link="./checks/invalid_curators.html")))
    doc.add_paragraph(str(Inline("Δωρητές με παράξενα ονόματα", link="./checks/invalid_donors.html")))

    doc.add_paragraph(str(Inline("Προβληματικά ISBN", link="./checks/invalid_isbn.html")))

    doc.add_paragraph(str(Inline("Δωρητές", link="./checks/donors.html")))

    with open(os.path.join(reports_directory, "index.md"), "w", encoding="utf-8") as outfile:
        outfile.write(str(doc))


def main():
    """Create markdown reports"""
    if len(sys.argv) > 0:
        md_report_dir = os.path.abspath(sys.argv[1])
    else:
        md_report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir, "md_reports")
    print(f"Creating reports in {md_report_dir}")
    shutil.rmtree(md_report_dir, ignore_errors=True)
    add_index(md_report_dir)
    report_weird_names(md_report_dir)
    report_donors(md_report_dir)
    report_isbns(md_report_dir)
    report_entry_numbers(md_report_dir)
    report_entries(md_report_dir)
    report_single_fields(md_report_dir)
    report_single_extracted_fields(md_report_dir)
    report_invalid_dewey(md_report_dir)
    print(f"Finished creating reports in {md_report_dir}")


if __name__ == "__main__":
    main()
