import os
from typing import Any, Dict

from sayou.assembler.pipeline import AssemblerPipeline
from sayou.chunking.pipeline import ChunkingPipeline
from sayou.connector.pipeline import ConnectorPipeline
from sayou.core.base_component import BaseComponent
from sayou.core.decorators import measure_time, safe_run
from sayou.core.schemas import SayouOutput
from sayou.document.pipeline import DocumentPipeline
from sayou.loader.pipeline import LoaderPipeline
from sayou.refinery.pipeline import RefineryPipeline
from sayou.wrapper.pipeline import WrapperPipeline

from ..core.config import SayouConfig


class StandardPipeline(BaseComponent):
    """
    (Tier 1) The All-in-One ETL Orchestrator.

    Automates the entire journey from raw data to database:
    Connector -> Document -> Refinery -> Chunking -> Wrapper -> Assembler -> Loader
    """

    component_name = "StandardPipeline"

    def __init__(
        self,
        extra_generators=None,
        extra_fetchers=None,
        extra_parsers=None,
        extra_normalizers=None,
        extra_processors=None,
        extra_splitters=None,
        extra_adapters=None,
        extra_builders=None,
        extra_writers=None,
        config: Dict[str, Any] = None,
        **kwargs,
    ):
        """
        Initializes the Brain. Plugins are passed directly to sub-pipelines.
        """
        super().__init__()

        full_config = config or {}
        full_config.update(kwargs)
        self.config = SayouConfig(full_config)
        cfg = self.config

        self.connector = ConnectorPipeline(
            extra_generators=extra_generators,
            extra_fetchers=extra_fetchers,
            **cfg.connector,
        )
        self.document = DocumentPipeline(
            extra_parsers=extra_parsers,
            **cfg.document,
        )
        self.refinery = RefineryPipeline(
            extra_normalizers=extra_normalizers,
            processors=extra_processors,
            **cfg.refinery,
        )
        self.chunking = ChunkingPipeline(
            extra_splitters=extra_splitters,
            **cfg.chunking,
        )
        self.wrapper = WrapperPipeline(
            extra_adapters=extra_adapters,
            **cfg.wrapper,
        )
        self.assembler = AssemblerPipeline(
            extra_builders=extra_builders,
            **cfg.assembler,
        )
        self.loader = LoaderPipeline(
            extra_writers=extra_writers,
            **cfg.loader,
        )

        self.initialize(**kwargs)

    @classmethod
    def process(
        cls,
        source: str,
        destination: str = None,
        strategies: Dict[str, str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        [Facade] 1-Line Execution.

        Usage:
            StandardPipeline.process(
                "https://...",
                extra_splitters=[MySplitter],
                chunk_size=500
            )
        """
        instance = cls(**kwargs)
        return instance.ingest(source, destination, strategies, **kwargs)

    @safe_run(default_return=None)
    def initialize(self, config: Dict[str, Any] = None, **kwargs):
        """
        [Standard] Initialize all sub-pipelines with new configurations.

        This allows re-configuring the pipeline without recreating it.
        e.g. pipeline.initialize(chunk_size=1000)
        """
        if config:
            self.config._config.update(config)
        self.config._config.update(kwargs)

        cfg = self.config

        self.connector.initialize(**cfg.connector)
        self.document.initialize(**cfg.document)
        self.refinery.initialize(**cfg.refinery)
        self.chunking.initialize(**cfg.chunking)
        self.wrapper.initialize(**cfg.wrapper)
        self.assembler.initialize(**cfg.assembler)
        self.loader.initialize(**cfg.loader)

        self._log("StandardPipeline initialized. Configs propagated.")

    @measure_time
    def ingest(
        self,
        source: str,
        destination: str = None,
        strategies: Dict[str, str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Execute the full ETL pipeline.
        """
        strategies = strategies or {}

        # Destination Defaulting
        if not destination:
            base_name = os.path.basename(source) if source else "output"
            if not base_name or "://" in source:
                base_name = "sayou_output"
            destination = f"./{os.path.splitext(base_name)[0]}.json"
            self._log(f"No destination provided. Defaulting to: {destination}")

        accumulated_nodes = []
        stats = {"processed": 0, "failed": 0, "files_count": 0}

        # Runtime Config Merge (Highest Priority)
        run_config = {**self.config._config, **kwargs}

        self._log(f"--- Starting Ingestion: {source} -> {destination} ---")

        # 1. Connector
        packets = self.connector.run(
            source, strategy=strategies.get("connector", "auto"), **run_config
        )

        # -----------------------------------------------------------
        # Loop: Process each file individually
        # -----------------------------------------------------------
        for packet in packets:
            stats["files_count"] += 1
            if not packet.success:
                self._log(f"Fetch failed: {packet.error}", level="warning")
                stats["failed"] += 1
                continue

            try:
                # Meta
                file_name = packet.task.meta.get("filename", "unknown_source")
                raw_data = packet.data

                # 2. Document
                doc_obj = None
                if isinstance(raw_data, bytes):
                    try:
                        doc_obj = self.document.run(
                            raw_data,
                            file_name,
                            strategy=strategies.get("document", "auto"),
                            **run_config,
                        )
                    except Exception as e:
                        self._log(
                            f"No binary parser for {file_name}. Fallback to text decoding.",
                            level="debug",
                        )
                        try:
                            raw_data = raw_data.decode("utf-8")
                        except UnicodeDecodeError:
                            self._log(
                                f"Failed to decode {file_name}. It might be an unsupported binary.",
                                level="error",
                            )
                            stats["failed"] += 1
                            continue

                refine_input = doc_obj if doc_obj else raw_data

                # 3. Refinery
                ref_strat = strategies.get("refinery")
                if not ref_strat:
                    ref_strat = "standard_doc" if doc_obj else "auto"

                blocks = self.refinery.run(
                    refine_input, strategy=ref_strat, **run_config
                )
                if not blocks:
                    continue

                # 4. Chunking
                all_chunks = []
                chunk_strat = strategies.get("chunking", "auto")
                all_chunks = self.chunking.run(
                    blocks, strategy=chunk_strat, **run_config
                )

                if all_chunks:
                    self._log(f"\n[DEBUG] File: {file_name}")
                    self._log(f" - Total Chunks: {len(all_chunks)}")
                    for i, chunk in enumerate(all_chunks[:3]):
                        c_data = (
                            chunk.model_dump()
                            if hasattr(chunk, "model_dump")
                            else chunk
                        )
                        self._log(
                            f" - Chunk[{i}] ID: {c_data.get('metadata', {}).get('chunk_id')}"
                        )
                        self._log(
                            f" - Chunk[{i}] Parent: {c_data.get('metadata', {}).get('parent_id')}"
                        )
                    self._log("--------------------------------------------------\n")

                if not all_chunks:
                    continue

                # 5. Wrapper
                wrap_strat = strategies.get("wrapper", "auto")
                wrapper_out = self.wrapper.run(
                    all_chunks, strategy=wrap_strat, **run_config
                )

                if wrapper_out and wrapper_out.nodes:
                    accumulated_nodes.extend(wrapper_out.nodes)
                    stats["processed"] += 1

            except Exception as e:
                self._log(f"Pipeline Error on {packet.task.uri}: {e}", level="error")
                stats["failed"] += 1

        # -----------------------------------------------------------
        # Finalize: Assemble & Load ONCE
        # -----------------------------------------------------------
        if not accumulated_nodes:
            self._log("No nodes generated from any source.", level="warning")
            return stats

        self._log(
            f"Accumulated {len(accumulated_nodes)} nodes from {stats['processed']} files. assembling..."
        )

        try:
            final_output = SayouOutput(
                nodes=accumulated_nodes,
                metadata={"source_count": stats["processed"], "origin": source},
            )

            # 6. Assembler
            asm_strat = strategies.get("assembler", "auto")
            payload = self.assembler.run(final_output, strategy=asm_strat, **run_config)

            # 7. Loader
            load_strat = strategies.get("loader", "auto")
            success = self.loader.run(
                payload, destination, strategy=load_strat, **run_config
            )

            if not success:
                self._log("Final Write failed.", level="error")

        except Exception as e:
            self._log(f"Final Assembly/Load Error: {e}", level="error")
            stats["failed"] += 1

        self._log(f"--- Ingestion Complete. Stats: {stats} ---")
        return stats
