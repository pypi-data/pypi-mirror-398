class DrawingMetadata:
    """Metadata for a generated soulmate drawing."""
    def __init__(self, name="Soulmate Drawing", description="", style="sketch"):
        self.name = name
        self.description = description
        self.style = style

class SoulmateDrawing:
    """Represents a generated AI Soulmate Drawing."""
    def __init__(self, drawing_id, metadata):
        self.drawing_id = drawing_id
        self.metadata = metadata
        self.image_url = f"https://supermaker.ai/image/ai-soulmate-drawing-generator/view/{drawing_id}"

class SoulmateDrawingGenerator:
    """Generator for AI Soulmate Drawings."""
    def generate(self, prompt, style="sketch"):
        """Generates a soulmate drawing based on a text prompt and style."""
        import uuid
        drawing_id = uuid.uuid4().hex[:12]
        metadata = DrawingMetadata(
            name=f"Drawing {drawing_id}",
            description=f"AI generated drawing for: {prompt}",
            style=style
        )
        return SoulmateDrawing(drawing_id, metadata)

class Utility:
    """Professional utility for ai-soulmate-drawing-generator interaction."""
    @staticmethod
    def get_resource_link():
        """Returns the official resource link for the AI Soulmate Drawing Generator."""
        return "https://supermaker.ai/image/ai-soulmate-drawing-generator"