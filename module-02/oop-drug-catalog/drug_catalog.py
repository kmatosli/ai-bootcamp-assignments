"""
drug_catalog.py — Object-oriented drug catalog for Caduceus.

Maps the bootcamp Module 2 OOP assignment ("Library Catalog with Book / EBook /
Catalog") onto Caduceus's real domain:

    Book      -> Drug              (small molecule, single active prescription per patient)
    EBook     -> BiologicDrug      (biologic — supports concurrent indications per patient)
    Catalog   -> DrugCatalog       (the universe of approved drugs we track)

The mapping is faithful to the assignment:

  * Book.checked_out (bool)   -> Drug.in_use (bool)       single concurrent dispense
  * EBook check-out by many   -> BiologicDrug.active_indications (counter)
                                 a biologic can be approved for multiple indications
                                 and a patient can be on it for more than one
  * search_by_author          -> search_by_manufacturer
  * search_by_title           -> search_by_name
  * get_available             -> get_available           (drugs not currently in use)
  * summary                   -> summary

Bonus (Dunder Methods Deep Dive) also implemented:
  __eq__, __lt__, __len__, __contains__

Run:
    python drug_catalog.py
"""
from __future__ import annotations

from typing import List


# ──────────────────────────────────────────────────────────────────────────────
# Drug — base class (maps to Book in the assignment spec)
# ──────────────────────────────────────────────────────────────────────────────

class Drug:
    """A small-molecule drug in the Caduceus universe.

    Bootcamp mapping: this is the Book class. We add a few attributes that
    matter for Caduceus (manufacturer, application_number, pages_of_label)
    while preserving the assignment's required shape:

      * title  -> name
      * author -> manufacturer
      * year   -> approval_year
      * checked_out (bool) -> in_use (bool)
      * check_out() / return_book() -> dispense() / return_drug()
    """

    def __init__(
        self,
        name: str,
        manufacturer: str,
        approval_year: int,
        pages_of_label: int = 0,
    ) -> None:
        if not isinstance(approval_year, int) or approval_year <= 0:
            raise ValueError(
                f"approval_year must be a positive integer, got {approval_year!r}"
            )
        self.name = name
        self.manufacturer = manufacturer
        self.approval_year = approval_year
        self.pages_of_label = pages_of_label
        self.in_use: bool = False  # spec: "starts False"

    # ── Required methods ─────────────────────────────────────────────────────

    def dispense(self) -> None:
        """Mark the drug as currently dispensed to a patient."""
        if self.in_use:
            print(f"  ⚠ {self.name} is already dispensed.")
            return
        self.in_use = True
        print(f"  ✓ Dispensed: {self.name}")

    def return_drug(self) -> None:
        """Return the drug (e.g., end of course)."""
        if not self.in_use:
            print(f"  ⚠ {self.name} is not currently dispensed.")
            return
        self.in_use = False
        print(f"  ✓ Returned: {self.name}")

    # ── Rubric-compatibility aliases ─────────────────────────────────────────
    # The bootcamp rubric uses Book / EBook / Catalog vocabulary (check_out,
    # return_book). These aliases delegate to the Caduceus-named methods so
    # the rubric's verbatim test snippet runs without modification.

    def check_out(self) -> None:
        """Rubric alias for dispense() — see Drug.dispense."""
        self.dispense()

    def return_book(self) -> None:
        """Rubric alias for return_drug() — see Drug.return_drug."""
        self.return_drug()

    # ── Dunder methods (bonus: Dunder Methods Deep Dive) ─────────────────────

    def __repr__(self) -> str:
        status = "dispensed" if self.in_use else "available"
        return f"<Drug {self.name!r} by {self.manufacturer} ({status})>"

    def __eq__(self, other: object) -> bool:
        # Spec: compare by title and author -> name and manufacturer
        if not isinstance(other, Drug):
            return NotImplemented
        return (
            self.name == other.name
            and self.manufacturer == other.manufacturer
        )

    def __lt__(self, other: "Drug") -> bool:
        # Spec: sort by title -> sort by name
        if not isinstance(other, Drug):
            return NotImplemented
        return self.name < other.name

    def __hash__(self) -> int:
        # Required because __eq__ is defined; lets Drug live in sets/dict keys
        return hash((self.name, self.manufacturer))

    def __len__(self) -> int:
        # Spec: return number of pages -> use pages_of_label
        return self.pages_of_label

    def __contains__(self, keyword: str) -> bool:
        # Spec: "keyword" in book to search the title -> search the name
        return keyword.lower() in self.name.lower()


# ──────────────────────────────────────────────────────────────────────────────
# BiologicDrug — subclass (maps to EBook in the assignment spec)
# ──────────────────────────────────────────────────────────────────────────────

class BiologicDrug(Drug):
    """A biologic drug — can support multiple concurrent active indications.

    Bootcamp mapping: this is the EBook class. The assignment says an ebook
    can be checked out by multiple people simultaneously, hint: use a counter
    instead of a boolean.

    Caduceus mapping: biologics (mAbs, ADCs, vaccines) are routinely approved
    for multiple indications and a single patient may be on the biologic for
    more than one indication at the same time (e.g., Humira for both
    rheumatoid arthritis and Crohn's). We track that as a counter of
    currently-active indications.
    """

    def __init__(
        self,
        name: str,
        manufacturer: str,
        approval_year: int,
        modality: str = "mAb",
        pages_of_label: int = 0,
    ) -> None:
        super().__init__(name, manufacturer, approval_year, pages_of_label)
        self.modality = modality           # mAb / ADC / vaccine / protein / etc.
        self.active_indications: int = 0   # spec: counter, not boolean

    # ── Override check-out (spec: ebooks can be checked out by many) ─────────

    def dispense(self) -> None:
        self.active_indications += 1
        print(
            f"  ✓ Dispensed biologic: {self.name} "
            f"(now active for {self.active_indications} indication"
            f"{'s' if self.active_indications != 1 else ''})"
        )

    def return_drug(self) -> None:
        if self.active_indications == 0:
            print(f"  ⚠ {self.name} has no active indications to return.")
            return
        self.active_indications -= 1
        print(
            f"  ✓ Returned biologic: {self.name} "
            f"({self.active_indications} indication"
            f"{'s' if self.active_indications != 1 else ''} still active)"
        )

    # The base class's `in_use` is also kept consistent for polymorphism with
    # the catalog's get_available() — a biologic is "in use" if at least one
    # indication is active.
    @property  # type: ignore[override]
    def in_use(self) -> bool:  # type: ignore[override]
        return self.active_indications > 0

    @in_use.setter
    def in_use(self, value: bool) -> None:
        # Allow base __init__ to set in_use=False without blowing up
        if value is False:
            self.active_indications = 0

    def __repr__(self) -> str:
        return (
            f"<BiologicDrug {self.name!r} by {self.manufacturer} "
            f"[{self.modality}] (active in {self.active_indications} indication"
            f"{'s' if self.active_indications != 1 else ''})>"
        )


# ──────────────────────────────────────────────────────────────────────────────
# DrugCatalog — collection class (maps to Catalog)
# ──────────────────────────────────────────────────────────────────────────────

class DrugCatalog:
    """The universe of drugs Caduceus tracks.

    Bootcamp mapping: Catalog class. Methods are renamed to fit the domain:

      add_book           -> add_drug
      search_by_author   -> search_by_manufacturer
      search_by_title    -> search_by_name
      get_available      -> get_available
      summary            -> summary
    """

    def __init__(self) -> None:
        self.drugs: List[Drug] = []

    # Spec uses `books` as the attribute name — alias for compatibility with
    # the assignment's test snippet (`catalog.books[0].check_out()`).
    @property
    def books(self) -> List[Drug]:
        return self.drugs

    def add_drug(self, drug: Drug) -> None:
        if not isinstance(drug, Drug):
            raise TypeError(f"Expected Drug, got {type(drug).__name__}")
        self.drugs.append(drug)

    def search_by_manufacturer(self, manufacturer: str) -> List[Drug]:
        """All drugs made by a given manufacturer."""
        return [d for d in self.drugs if d.manufacturer == manufacturer]

    def search_by_name(self, keyword: str) -> List[Drug]:
        """All drugs whose name contains `keyword` (case-insensitive, anywhere)."""
        kw = keyword.lower()
        return [d for d in self.drugs if kw in d.name.lower()]

    def get_available(self) -> List[Drug]:
        """Drugs not currently dispensed (in_use == False)."""
        return [d for d in self.drugs if not d.in_use]

    def summary(self) -> None:
        total = len(self.drugs)
        small_molecule = sum(1 for d in self.drugs if not isinstance(d, BiologicDrug))
        biologics = sum(1 for d in self.drugs if isinstance(d, BiologicDrug))
        available = len(self.get_available())
        print()
        print("─" * 60)
        print(f"  DRUG CATALOG SUMMARY")
        print("─" * 60)
        print(f"  Total drugs:        {total}")
        print(f"    Small molecules:  {small_molecule}")
        print(f"    Biologics:        {biologics}")
        print(f"  Currently available: {available}")
        print(f"  Currently in use:    {total - available}")
        print("─" * 60)

    # ── Rubric-compatibility aliases ─────────────────────────────────────────
    # The bootcamp rubric uses Catalog vocabulary (add_book, search_by_author,
    # search_by_title). These aliases delegate to the Caduceus-named methods
    # so the rubric's verbatim test snippet runs without modification.

    def add_book(self, drug: Drug) -> None:
        """Rubric alias for add_drug() — see DrugCatalog.add_drug."""
        self.add_drug(drug)

    def search_by_author(self, author: str) -> List[Drug]:
        """Rubric alias for search_by_manufacturer()."""
        return self.search_by_manufacturer(author)

    def search_by_title(self, keyword: str) -> List[Drug]:
        """Rubric alias for search_by_name()."""
        return self.search_by_name(keyword)


# ──────────────────────────────────────────────────────────────────────────────
# Demo / test harness — exercises every required behavior
# ──────────────────────────────────────────────────────────────────────────────

def _demo() -> None:
    print("=" * 60)
    print("  CADUCEUS DRUG CATALOG — Module 2 OOP demo")
    print("=" * 60)

    # Build the catalog
    catalog = DrugCatalog()

    # Real Phase 1 universe drugs
    catalog.add_drug(Drug("Eliquis",  "Bristol-Myers Squibb", 2012, pages_of_label=42))
    catalog.add_drug(Drug("Xeljanz",  "Pfizer",               2012, pages_of_label=38))
    catalog.add_drug(Drug("Mounjaro", "Eli Lilly",            2022, pages_of_label=51))
    catalog.add_drug(BiologicDrug("Keytruda", "Merck",     2014, modality="mAb",     pages_of_label=89))
    catalog.add_drug(BiologicDrug("Humira",   "AbbVie",    2002, modality="mAb",     pages_of_label=104))
    catalog.add_drug(BiologicDrug("Enhertu",  "AstraZeneca", 2019, modality="ADC",   pages_of_label=67))

    # ── Search by name (the spec test) ─────────────────────────────────────
    print("\n[1] search_by_name('eli'):")
    for d in catalog.search_by_name("eli"):
        print(f"    {d!r}")

    # ── Search by manufacturer ─────────────────────────────────────────────
    print("\n[2] search_by_manufacturer('Pfizer'):")
    for d in catalog.search_by_manufacturer("Pfizer"):
        print(f"    {d!r}")

    # ── Dispense / return — small-molecule (bool semantics) ────────────────
    print("\n[3] Dispense Eliquis (small molecule — bool):")
    catalog.drugs[0].dispense()
    catalog.drugs[0].dispense()        # already dispensed — should warn
    catalog.drugs[0].return_drug()

    # ── Dispense / return — biologic (counter semantics) ───────────────────
    print("\n[4] Dispense Keytruda for two indications (biologic — counter):")
    keytruda = catalog.search_by_name("keytruda")[0]
    keytruda.dispense()                # NSCLC indication
    keytruda.dispense()                # melanoma indication
    print(f"    Active indications: {keytruda.active_indications}")
    keytruda.return_drug()
    print(f"    Active indications: {keytruda.active_indications}")

    # ── Availability check ─────────────────────────────────────────────────
    available = catalog.get_available()
    print(f"\n[5] get_available(): {len(available)} drugs not in use")
    for d in available:
        print(f"    {d!r}")

    # ── Year validation ────────────────────────────────────────────────────
    print("\n[6] Validation — year must be positive int:")
    for bad_year in (-1, 0, 2024.5, "2024"):
        try:
            Drug("BadDrug", "BadCo", bad_year)  # type: ignore[arg-type]
            print(f"    ✗ year={bad_year!r} should have raised, did not")
        except (ValueError, TypeError) as e:
            print(f"    ✓ year={bad_year!r} correctly rejected: {type(e).__name__}")

    # ── Dunder methods deep dive (bonus) ───────────────────────────────────
    print("\n[7] Dunder methods deep dive (bonus):")

    # __eq__
    same = Drug("Eliquis", "Bristol-Myers Squibb", 2012)
    print(f"    __eq__:  Eliquis == new Eliquis instance? {catalog.drugs[0] == same}")

    # __lt__ + sorted()
    sorted_drugs = sorted(catalog.drugs)
    print(f"    __lt__:  sorted by name -> {[d.name for d in sorted_drugs]}")

    # __len__
    print(f"    __len__: len(Eliquis) = {len(catalog.drugs[0])} pages of label")

    # __contains__
    print(f"    __contains__: 'eli' in Eliquis drug object? {'eli' in catalog.drugs[0]}")

    # ── Final summary ──────────────────────────────────────────────────────
    catalog.summary()

    # ── Rubric-aliases smoke test ─────────────────────────────────────────
    # Demonstrate that the rubric's verbatim method names work, mapped to the
    # Caduceus domain (Drug = Book, BiologicDrug = EBook, DrugCatalog = Catalog).
    print("\n[8] Rubric-aliases smoke test:")
    rubric_cat = DrugCatalog()
    rubric_cat.add_book(Drug("Python Crash Course", "Eric Matthes", 2019))
    rubric_cat.add_book(Drug("Clean Code", "Robert Martin", 2008))
    rubric_cat.add_book(BiologicDrug("AI Engineering", "Chip Huyen", 2025, modality="ADC"))

    results = rubric_cat.search_by_title("python")
    print(f"    search_by_title('python') -> {results}")

    rubric_cat.books[0].check_out()
    available = rubric_cat.get_available()
    print(f"    Available: {len(available)} books")


if __name__ == "__main__":
    _demo()
