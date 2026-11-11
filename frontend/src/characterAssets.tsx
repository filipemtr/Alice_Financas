import {useState} from 'react'
import type {Theme} from './types'

// Images are existing transparent PNGs on third-party websites, not AI-generated.
// All source pages state personal/non-commercial usage. Please verify permission
// before using this project commercially. See docs/IMAGENS.md for source credits.
const IMAGES:Record<Theme,{name:string;source:string;url:string}>={
  kitty:{name:'Hello Kitty',source:'https://www.citypng.com/photo/86daad56/sweet-portrait-of-hello-kitty-waving-hd-transparent-png',url:'https://www.citypng.com/public/uploads/preview/sweet-portrait-of-hello-kitty-waving-hd-transparent-png-735811696611595jr36apxzjp.png?v=2025103105'},
  pony:{name:'Fluttershy',source:'https://www.clipartmax.com/middle/m2i8b1d3G6A0A0b1_fluttershy-happy-by-the3javi-fluttershy-face-happy-mlp-fluttershy-standing/',url:'https://www.clipartmax.com/png/middle/199-1990134_fluttershy-happy-by-the3javi-fluttershy-face-happy-mlp-fluttershy-standing.png'},
  snoopy:{name:'Snoopy',source:'https://pnggallery.com/snoopy/',url:'https://pnggallery.com/wp-content/uploads/snoopy-01.png'},
  amelie:{name:'Amélie Poulain',source:'https://www.pngwing.com/ca/free-png-ikcho',url:'https://w7.pngwing.com/pngs/627/860/png-transparent-amelie-poulain-computer-icons-others-child-face-black-hair.png'},
  coraline:{name:'Coraline',source:'https://pnggallery.com/coraline/',url:'https://pnggallery.com/wp-content/uploads/coraline-01.png'},
}
export const DECORATIVE_SOURCES=(Object.keys(IMAGES) as Theme[]).map(key=>({name:IMAGES[key].name,page:IMAGES[key].source}))

/** Local asset first; fall back to the publisher URL if an asset has not been downloaded. */
export function CharacterArt({theme,className=''}:{theme:Theme;className?:string}){
  const {name,url}=IMAGES[theme]
  const [attempt,setAttempt]=useState<{theme:Theme;remote:boolean;failed:boolean}>({theme,remote:false,failed:false})
  // A newly selected theme always starts with its own local PNG, not the
  // previously selected theme's remote URL.
  const current=attempt.theme===theme?attempt:{theme,remote:false,failed:false}
  return current.failed
    ? <span role="img" aria-label={name} className={`${className} character-fallback`}>{({kitty:'🎀',pony:'🌈',snoopy:'☁️',amelie:'🌷',coraline:'🌙'} as Record<Theme,string>)[theme]}</span>
    : <img key={`${theme}-${current.remote?'remote':'local'}`} className={`${className} character-art`}
       src={current.remote?url:`/characters/${theme}.png`}
       alt={name} decoding="async" loading="lazy" draggable={false} referrerPolicy="no-referrer"
       onError={()=>setAttempt({theme,remote:true,failed:current.remote})}/>
}
