from tripplanner import TripPlanner
import sys
from pprint import pprint

def get_thinned_directions(all_directions):
    all_paths = []
    for direction in all_directions:
        directions = []
        for step in direction['legs'][0]['steps']:
            pprint(step)
            if 'steps' not in step:
                directions.append({'major': step['html_instructions'], 'steps': None})
            else:
                major = {'major': step['html_instructions'], 'steps': []}
                for minor_step in step['steps']:
                    major['steps'].append(minor_step['html_instructions'])
                directions.append(major)
        all_paths.append(directions)
    return all_paths

def main():
    trip_planner = TripPlanner("Siebel Center for Computer Science", "Illinois Street Residence Halls")
    trip_planner.search()
    pprint(get_thinned_directions(trip_planner.get_directions()))

if __name__ == "__main__":
    sys.exit(main())
