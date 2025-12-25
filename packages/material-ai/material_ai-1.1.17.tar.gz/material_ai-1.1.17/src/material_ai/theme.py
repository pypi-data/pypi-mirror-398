from pydantic import BaseModel, Field


class PrimaryPalette(BaseModel):
    main: str


class BackgroundPalette(BaseModel):
    default_: str = Field(alias="default")
    paper: str
    card: str
    cardHover: str
    history: str


class TextPalette(BaseModel):
    primary: str
    secondary: str
    tertiary: str
    h5: str
    selected: str
    tagline: str


class TooltipPalette(BaseModel):
    background: str
    text: str


class ThemePalette(BaseModel):
    mode: str
    primary: PrimaryPalette
    background: BackgroundPalette
    text: TextPalette
    tooltip: TooltipPalette


class ThemeConfig(BaseModel):
    lightPalette: ThemePalette
    darkPalette: ThemePalette
