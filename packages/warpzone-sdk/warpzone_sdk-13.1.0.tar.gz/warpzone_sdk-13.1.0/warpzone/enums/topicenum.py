from enum import Enum


class Topic(Enum):
    INGRESS = "ingress"
    LANDING = "landing"
    UNIFORM = "uniform"
    DEPARTURE = "departure"
    EGRESS = "egress"
    EVENTS = "events"
    FEATURES = "features"
