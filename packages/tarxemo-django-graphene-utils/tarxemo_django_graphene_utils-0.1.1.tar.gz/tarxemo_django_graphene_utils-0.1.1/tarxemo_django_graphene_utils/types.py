import graphene

class LocationInput(graphene.InputObjectType):
    """Input type for location coordinates"""
    latitude = graphene.Float(required=True, description="Latitude in decimal degrees")
    longitude = graphene.Float(required=True, description="Longitude in decimal degrees")
    radius = graphene.Float(description="Search radius in kilometers")

class SeriesPoint(graphene.ObjectType):
    label = graphene.String()
    value = graphene.Float()
