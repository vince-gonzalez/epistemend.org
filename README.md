```
╔════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                            ║
║     ███████╗██████╗ ██╗███████╗████████╗███████╗███╗   ███╗███████╗███╗   ██╗██████╗       ║
║     ██╔════╝██╔══██╗██║██╔════╝╚══██╔══╝██╔════╝████╗ ████║██╔════╝████╗  ██║██╔══██╗      ║
║     █████╗  ██████╔╝██║███████╗   ██║   █████╗  ██╔████╔██║█████╗  ██╔██╗ ██║██║  ██║      ║
║     ██╔══╝  ██╔═══╝ ██║╚════██║   ██║   ██╔══╝  ██║╚██╔╝██║██╔══╝  ██║╚██╗██║██║  ██║      ║
║     ███████╗██║     ██║███████║   ██║   ███████╗██║ ╚═╝ ██║███████╗██║ ╚████║██████╔╝      ║
║     ╚══════╝╚═╝     ╚═╝╚══════╝   ╚═╝   ╚══════╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═══╝╚═════╝       ║
║                                                                                            ║
║                               one ORCID in, one document out                               ║
║                                                                                            ║
╚════════════════════════════════════════════════════════════════════════════════════════════╝
```

[www.epistemend.org](https://www.epistemend.org) checks a published record in
one pass. Paste an ORCID; it reports what the record says, where the work
actually lives, and what disagrees between them.

Nine checks run in the page. ORCID, OpenAlex, Zenodo and Wikidata all allow
cross-origin requests, so nothing goes through a server here and there is
nothing to log the query with.

| | |
|---|---|
| **Identity** | who else publishes under this name, and whether the ORCID is split across several index records |
| **The record** | what the author lists, against what the index files under their identifier |
| **Where it was published** | journal, repository, conference - or nowhere yet |
| **Citations** | how many are from other people, and how many are the author's own |
| **Reaching the index** | how long a deposit takes to arrive, and whether the ORCID survives the trip |
| **The knowledge graph** | whether an item exists, and whether it knows whose work it is |
| **Deposit integrity** | the metadata faults that need a correction once a DOI is permanent |
| **Abstracts** | whether the copies in two places still say the same thing |
| **Retractions** | anything on the record marked retracted |

Nothing is scored, ranked or graded. Each section states what it found and
what it could not reach, because the same fact means different things for a
first-year student and a professor of thirty years.

## The rest of it

Three checks need something a browser cannot have - the deposited files, a
dependency graph, a repository to read - and a browser cannot resolve outbound
links either. Those are named on the page rather than left out, and they run
on the command line:

    pip install authorecon
    authorecon-report 0000-0002-1825-0097

Nineteen checks, no dependencies, standard library only.
[vince-gonzalez/apriori](https://github.com/vince-gonzalez/apriori).

The two implementations are kept in agreement deliberately. Writing the second
one is what found the defects in the first: they disagreed on four numbers, and
every disagreement was a bug - in both directions.

If you arrived here from a citation, `Potica_in_America.pdf` is the file you
are probably looking for.

---

```
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║      ███████╗      ██╗  ██╗███████╗██╗   ██╗███████╗       ║
║      ██╔════╝      ██║ ██╔╝██╔════╝╚██╗ ██╔╝██╔════╝       ║
║      █████╗  █████╗█████╔╝ █████╗   ╚████╔╝ ███████╗       ║
║      ██╔══╝  ╚════╝██╔═██╗ ██╔══╝    ╚██╔╝  ╚════██║       ║
║      ██║           ██║  ██╗███████╗   ██║   ███████║       ║
║      ╚═╝           ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝       ║
║                                                            ║
║               ·   C  R  E  A  T  I  V  E   ·               ║
║                                                            ║
║          ────────────────────────────────────────          ║
║                                                            ║
║                      Vincent Gonzalez                      ║
║                         f-keys.com                         ║
║                 ORCID 0009-0005-3640-014X                  ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

Part of [F-Keys](https://f-keys.com) — independent hardware, software
and internet products. See the [working log](https://f-keys.com/log/)
and [live status](https://f-keys.com/status/).
