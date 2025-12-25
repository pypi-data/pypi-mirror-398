from pype.misc import xopen
from pype.exceptions import SnippetError


class fastq:
    """Fastq iterator to extract name, sequence and quality ofr each read."""

    def __init__(self, f, n=-1):
        """
        Specify the file object to iterate.

        :param f: fastq file
        :type f: File
        :param n: number of reads to evaluate, defaults to -1
        :type n: int, optional
        """

        self.fastq = f
        self.n = n
        self.counter = 0

    def __iter__(self):
        return self

    def __next__(self):
        """
        Read the next 4 lines of the fastq file.

        Implement a __next__ magic method to iterate the fastq file
        and return a dictionary with 'name', 'seq' 'sep' and 'qual' keys.
        The 'sep' line is collected for consistency, despite the fact that
        there may be no use for it.

        :raises StopIteration: Maximum umber of reads reached.
        :raises e: End of the file.
        :return: A dictionary with 'name', 'seq' and 'qual' keys.
        :rtype: dict
        """

        if self.counter == self.n:
            raise StopIteration
        try:
            name = next(self.fastq).strip()
            read = next(self.fastq).strip()
            sep = next(self.fastq).strip()
            qual = next(self.fastq).strip()
            self.counter += 1
            return {"name": name, "seq": read, "sep": sep, "qual": qual}
        except StopIteration as e:
            raise e


def parse_fastq_name_illumina_1_8(line):
    line = line.split(" ")
    line = [item.split(":") for item in line]
    machine_id = line[0][0]
    if machine_id.startswith("@"):
        machine_id = machine_id[1:]
    flowcell_id = line[0][2]
    lane_nr = line[0][3]
    mate_nr = line[1][0]
    index_id = line[1][3]
    return {
        "machine_id": machine_id,
        "flowcell_id": flowcell_id,
        "lane": lane_nr,
        "mate": mate_nr,
        "index": index_id,
    }


def parse_fastq_name_illumina_1_4(line):
    line = line.split("#")
    line = [item.split(":") for item in line]
    machine_id = line[0][0]
    if machine_id.startswith("@"):
        machine_id = machine_id[1:]
    flowcell_id = None
    lane_nr = line[0][1]
    index_id, mate_nr = line[1][0].split("/")

    return {
        "machine_id": machine_id,
        "flowcell_id": flowcell_id,
        "lane": lane_nr,
        "mate": mate_nr,
        "index": index_id,
    }


def parse_fastq_name_illumina_no_index(line):
    line = line.split(":")
    machine_id = line[0]
    if machine_id.startswith("@"):
        machine_id = machine_id[1:]
    flowcell_id = None
    lane_nr = line[1]
    try:
        index_id, mate_nr = line[4].split("/")
    except ValueError:
        mate_nr = None
    finally:
        index_id = None

    return {
        "machine_id": machine_id,
        "flowcell_id": flowcell_id,
        "lane": lane_nr,
        "mate": mate_nr,
        "index": index_id,
    }


def fastq_name_info(fastq_file, n=50000, strict=False):
    reads_info = []
    with xopen(fastq_file, "rt") as fq:
        fastq_iter = fastq(fq, n)
        for item in fastq_iter:
            try:
                reads_info.append(parse_fastq_name_illumina_1_4(item["name"]))
            except IndexError:
                try:
                    reads_info.append(parse_fastq_name_illumina_1_8(item["name"]))
                except IndexError:
                    reads_info.append(parse_fastq_name_illumina_no_index(item["name"]))
    info = reads_info[0]

    if strict:
        all_same = True
        for item in reads_info:
            if item != info:
                all_same = False
        if all_same:
            return info
        raise SnippetError("Unsuccessful fastq parsing")

    return info
