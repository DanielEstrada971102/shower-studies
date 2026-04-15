from typing import List, Any
import numpy as np

stations = range(1, 5)
sectors = range(1, 15)
wheels = range(-2, 3)

def get_best_matches(reader: Any, station: int = 1) -> List[Any]:
    """
    Returns the best matching segments for each generator muon.

    :param reader: The reader object containing generator muons.
    :type reader: Any
    :param station: The station number. Default is 1.
    :type station: int
    :return: The best matching segments.
    :rtype: List[Any]
    """

    genmuons = reader.genmuons

    bestMatches = [None for igm in range(len(genmuons))]

    # This is what's done in Jaime's code: https://github.com/jaimeleonh/DTNtuples/blob/unifiedPerf/test/DTNtupleTPGSimAnalyzer_Efficiency.C#L181-L208
    # Basically: get the best matching segment to a generator muon per MB chamber

    # color_msg(f"[FUNCTIONS::GET_BEST_MATCHES] Debugging with station {station}", color = "red", indentLevel = 0)
    for igm, gm in enumerate(genmuons):
        # color_msg(f"[FUNCTIONS::GET_BEST_MATCHES] igm {igm}", indentLevel = 1)
        # gm.summarize(indentLevel = 2)
        for bestMatch in getattr(gm, 'matched_segments', []):
            if bestMatch.st == station:
                bestMatches[igm] = bestMatch

    # Remove those that are None which are simply dummy values
    bestMatches = list(filter(lambda key: key is not None, bestMatches))
    return bestMatches

def phiConv(phi: float) -> float:
    """
    Converts a phi value.

    :param phi: The phi value to convert.
    :type phi: float
    :return: The converted phi value.
    :rtype: float
    """
    return 0.5 * phi / 65536.0


def correct_g4digi_time(g4digi: Any) -> float:
    """
    Correct the time of the digi by simulating the drift time.
    
    :param g4digi: The g4digi object with a _time attribute
    :type g4digi: Any
    :return: The corrected time
    :rtype: float
    """
    # ----- mimic the Javi's Code ----
    # simulate drift time

    mean, stddev = 175, 75
    time_offset = 400
    delay = np.random.normal(loc=mean, scale=stddev)
    return g4digi._time + abs(delay) + time_offset # why abs ?

def duplicate_particle_collection(event: Any, pcollection_name: str, new_pcollection_name: str) -> None:
    """
    Duplicates a particle collection in the event.

    :param event: The event object containing the particle collection.
    :type event: Any
    :param pcollection_name: The name of the particle collection to duplicate.
    :type pcollection_name: str
    :param new_pcollection_name: The name of the new duplicated particle collection.
    :type new_pcollection_name: str
    """
    if not hasattr(event, pcollection_name):
        raise AttributeError(f"The event does not have a particle collection named '{pcollection_name}'")
    setattr(event, new_pcollection_name, getattr(event, pcollection_name))