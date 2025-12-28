from typing import List

from pygeai.lab.models import ReasoningStrategy, LocalizedDescription, ReasoningStrategyList


class ReasoningStrategyMapper:
    @classmethod
    def _map_localized_descriptions(cls, descriptions_data: List[dict]) -> List[LocalizedDescription]:
        """
        Maps a list of localized description dictionaries to a list of LocalizedDescription objects.

        :param descriptions_data: List[dict] - List of dictionaries containing language and description.
        :return: List[LocalizedDescription] - List of mapped LocalizedDescription objects.
        """
        return [
            LocalizedDescription(
                language=desc.get("language"),
                description=desc.get("description")
            )
            for desc in descriptions_data
        ]

    @classmethod
    def map_to_reasoning_strategy(cls, data: dict) -> ReasoningStrategy:
        """
        Maps a dictionary to a ReasoningStrategy object with explicit field mapping.

        :param data: dict - The dictionary containing reasoning strategy details.
        :return: ReasoningStrategy - The mapped ReasoningStrategy object.
        """
        strategy_data = data.get("strategyDefinition", data)
        name = strategy_data.get("name")
        system_prompt = strategy_data.get("systemPrompt")
        access_scope = strategy_data.get("accessScope")
        type_ = strategy_data.get("type")
        localized_descriptions_data = strategy_data.get("localizedDescriptions")
        localized_descriptions = cls._map_localized_descriptions(localized_descriptions_data) if localized_descriptions_data else None
        id = strategy_data.get("id")

        return ReasoningStrategy(
            name=name,
            system_prompt=system_prompt,
            access_scope=access_scope,
            type=type_,
            localized_descriptions=localized_descriptions,
            id=id
        )

    @classmethod
    def map_to_reasoning_strategy_list(cls, data: dict) -> ReasoningStrategyList:
        strategy_list = []
        strategies = data.get("strategies") if isinstance(data, dict) else data if isinstance(data, list) else []
        if strategies and any(strategies):
            for strategy_data in strategies:
                strategy = cls.map_to_reasoning_strategy(strategy_data)
                strategy_list.append(strategy)

        return ReasoningStrategyList(strategies=strategy_list)