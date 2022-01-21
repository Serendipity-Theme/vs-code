# Serendipity.

### [Serendipity Theme](https://serendipitytheme.com)

![Preview](https://github.com/michael-andreuzza/wvsc-serendipity/blob/master/hero.png?raw=true)

# Installation

1. Open **Extensions** sidebar panel in VS Code. `View → Extensions`
2. Search for **`serendipity`**
3. Click **Install** to install it.
4. Code > Preferences > Color Theme >
 **serendipity-light - serendipity-dark - serendipity-dark-italic - serendipity-light-italic**
5. Optional: Use the recommended settings below for best experience

## Recommended Settings

```js
{
  // This is are my personal prefferences.
  "editor.fontFamily": "'IBM Plex Mono', monospace",
  "editor.fontSize": 18,
  "editor.lineHeight": 38,
  "editor.letterSpacing": 0.5,
  "files.trimTrailingWhitespace": true,
  "editor.fontWeight": "normal",
  "prettier.eslintIntegration": true,
  "editor.cursorStyle": "line",
  "editor.cursorWidth": 5,
  "editor.cursorBlinking": "phase",
  "editor.renderWhitespace": "all",
}
```
## To remove italics add add this snippet to your settings.json, this will disable italics.


```js
"editor.tokenColorCustomizations": {
  "[Serendipity]": {
    "textMateRules": [
      {
        "scope": [
          "comment",
          "entity.other.attribute-name",
          "entity.other.inherited-class",
          "support.function",
          "variable",
          "meta.directive.vue"
        ],
        "settings": {
          "fontStyle": ""
        }
      }
    ]
  }
}
```


## Colours
I have worked towards a color palette that would feel fine on the eyes when using retina screens, this color combination made it possible, thanks to the pastel colors used on dark mode instead of "neonish".

The theme is available for editors, shells, UI's and more coming up.

## Available Options
- Light Morning
- Dark Sunset
- Dark Midnight


### Midnight Version
![Preview](https://github.com/michael-andreuzza/wvsc-serendipity/blob/master/midnight.png?raw=true)
### Sunset Version
![Preview](https://github.com/michael-andreuzza/wvsc-serendipity/blob/master/sunset.png?raw=true)
## Morning Version
![Preview](https://github.com/michael-andreuzza/wvsc-serendipity/blob/master/morning.png?raw=true)


## Feedback

Anything you wonder just contact me, [@Mike_Andreuzza](https://twitter.com/Mike_Andreuzza) on twitter.
