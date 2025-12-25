import random
from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import List

from pymlga.gene import Gene, GeneFactory


@dataclass
class Chromosome:
    genes: List[Gene]

    def __post_init__(self):
        assert self.genes is not None
        assert None not in self.genes

    def __iter__(self):
        return iter(self.genes)


class ChromosomeFactory(ABC):

    @abstractmethod
    def spawn(self) -> Chromosome:  # pragma: no cover
        pass

    @abstractmethod
    def clone(self, chromosome: Chromosome) -> Chromosome:  # pragma: no cover
        pass

    @abstractmethod
    def crossover(self, chromosome1: Chromosome, chromosome2: Chromosome) -> Chromosome:  # pragma: no cover
        pass


@dataclass
class FixedLengthChromosomeFactory(ChromosomeFactory):

    gene_factory: GeneFactory
    length: int = 1

    def __post_init__(self):
        assert self.length > 0

    def spawn(self) -> Chromosome:
        return Chromosome(genes=[
            self.gene_factory.spawn()
            for _ in range(self.length)
        ])

    def clone(self, chromosome: Chromosome) -> Chromosome:
        return Chromosome(genes=[
            self.gene_factory.clone(gene)
            for gene in chromosome
        ])

    def crossover(self, chromosome1: Chromosome, chromosome2: Chromosome) -> Chromosome:
        return Chromosome(genes=[
            self.gene_factory.clone(random.choice(genes))
            for genes in zip(chromosome1.genes, chromosome2.genes)
        ])


@dataclass
class RandomLengthChromosomeFactory(ChromosomeFactory):

    gene_factory: GeneFactory
    min_length: int
    max_length: int
    shortening_rate: float = 0
    lengthening_rate: float = 0
    throttling_factor: int = 3

    def __post_init__(self):
        assert self.min_length >= 0
        assert self.max_length > self.min_length
        assert self.shortening_rate >= 0
        assert self.shortening_rate <= 1
        assert self.lengthening_rate >= 0
        assert self.lengthening_rate <= 1
        assert self.throttling_factor > 0

    def spawn(self) -> Chromosome:
        return Chromosome(genes=[
            self.gene_factory.spawn()
            for _ in range(random.randint(self.min_length, self.max_length))
        ])

    def clone(self, chromosome: Chromosome) -> Chromosome:
        return _clone(
            chromosome=chromosome,
            gene_factory=self.gene_factory,
            min_length=self.min_length,
            max_length=self.max_length,
            shortening_rate=self.shortening_rate,
            lengthening_rate=self.lengthening_rate,
            throttling_factor=self.throttling_factor
        )

    def crossover(self, chromosome1: Chromosome, chromosome2: Chromosome) -> Chromosome:
        return _clone(
            chromosome=random.choice([chromosome1, chromosome2]),
            gene_factory=self.gene_factory,
            min_length=self.min_length,
            max_length=self.max_length,
            shortening_rate=self.shortening_rate,
            lengthening_rate=self.lengthening_rate,
            throttling_factor=self.throttling_factor
        )


def _clone(
        chromosome: Chromosome,
        gene_factory: GeneFactory,
        min_length: int,
        max_length: int,
        shortening_rate: float,
        lengthening_rate: float,
        throttling_factor: int
) -> Chromosome:
    genes = [
        gene_factory.clone(gene)
        for gene in chromosome.genes
    ]
    target_length = _get_target_length(
        initial_length=len(genes),
        min_length=min_length,
        max_length=max_length,
        shortening_rate=shortening_rate,
        lengthening_rate=lengthening_rate,
        throttling_factor=throttling_factor
    )
    while len(genes) > target_length:
        index_to_remove = random.randint(0, len(genes) - 1) if len(genes) > 1 else 0
        assert 0 <= index_to_remove < len(genes), f'invalid index_to_remove {index_to_remove}, len(genes)={len(genes)}, target_length={target_length}, min_length={min_length}, max_length={max_length}'
        genes.pop(index_to_remove)
    while len(genes) < target_length:
        index_to_insert = random.randint(0, len(genes)) if len(genes) > 0 else 0
        genes.insert(index_to_insert, gene_factory.spawn())
    return Chromosome(genes=genes)


def _get_target_length(
        initial_length: int,
        min_length: int,
        max_length: int,
        shortening_rate: float,
        lengthening_rate: float,
        throttling_factor: int
) -> int:
    shortening = int((initial_length - min_length) * (random.random() ** throttling_factor)) + 1 \
        if (shortening_rate > 0 and random.random() < shortening_rate) \
        else 0
    lengthening = int((max_length - initial_length) * (random.random() ** throttling_factor)) + 1 \
        if (lengthening_rate > 0 and random.random() < lengthening_rate) \
        else 0
    return initial_length + lengthening - shortening
