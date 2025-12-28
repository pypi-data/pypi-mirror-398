import{d as P,L as v,em as G,I as r,bL as L,bQ as j,bO as O,bN as q,bP as _,en as k,bf as B,bh as a,bj as w,bs as M,bt as A,eo as T,bx as N,by as H,e as X,f as Y,h as I}from"./index-BwlMlHGj.js";const V={success:r(_,null),error:r(q,null),warning:r(O,null),info:r(j,null)},E=P({name:"ProgressCircle",props:{clsPrefix:{type:String,required:!0},status:{type:String,required:!0},strokeWidth:{type:Number,required:!0},fillColor:[String,Object],railColor:String,railStyle:[String,Object],percentage:{type:Number,default:0},offsetDegree:{type:Number,default:0},showIndicator:{type:Boolean,required:!0},indicatorTextColor:String,unit:String,viewBoxWidth:{type:Number,required:!0},gapDegree:{type:Number,required:!0},gapOffsetDegree:{type:Number,default:0}},setup(e,{slots:u}){const c=v(()=>{const o="gradient",{fillColor:t}=e;return typeof t=="object"?`${o}-${G(JSON.stringify(t))}`:o});function y(o,t,n,g){const{gapDegree:p,viewBoxWidth:f,strokeWidth:h}=e,l=50,b=0,s=l,i=0,S=2*l,x=50+h/2,m=`M ${x},${x} m ${b},${s}
      a ${l},${l} 0 1 1 ${i},-100
      a ${l},${l} 0 1 1 0,${S}`,$=Math.PI*2*l,C={stroke:g==="rail"?n:typeof e.fillColor=="object"?`url(#${c.value})`:n,strokeDasharray:`${Math.min(o,100)/100*($-p)}px ${f*8}px`,strokeDashoffset:`-${p/2}px`,transformOrigin:t?"center":void 0,transform:t?`rotate(${t}deg)`:void 0};return{pathString:m,pathStyle:C}}const d=()=>{const o=typeof e.fillColor=="object",t=o?e.fillColor.stops[0]:"",n=o?e.fillColor.stops[1]:"";return o&&r("defs",null,r("linearGradient",{id:c.value,x1:"0%",y1:"100%",x2:"100%",y2:"0%"},r("stop",{offset:"0%","stop-color":t}),r("stop",{offset:"100%","stop-color":n})))};return()=>{const{fillColor:o,railColor:t,strokeWidth:n,offsetDegree:g,status:p,percentage:f,showIndicator:h,indicatorTextColor:l,unit:b,gapOffsetDegree:s,clsPrefix:i}=e,{pathString:S,pathStyle:x}=y(100,0,t,"rail"),{pathString:m,pathStyle:$}=y(f,g,o,"fill"),C=100+n;return r("div",{class:`${i}-progress-content`,role:"none"},r("div",{class:`${i}-progress-graph`,"aria-hidden":!0},r("div",{class:`${i}-progress-graph-circle`,style:{transform:s?`rotate(${s}deg)`:void 0}},r("svg",{viewBox:`0 0 ${C} ${C}`},d(),r("g",null,r("path",{class:`${i}-progress-graph-circle-rail`,d:S,"stroke-width":n,"stroke-linecap":"round",fill:"none",style:x})),r("g",null,r("path",{class:[`${i}-progress-graph-circle-fill`,f===0&&`${i}-progress-graph-circle-fill--empty`],d:m,"stroke-width":n,"stroke-linecap":"round",fill:"none",style:$}))))),h?r("div",null,u.default?r("div",{class:`${i}-progress-custom-content`,role:"none"},u.default()):p!=="default"?r("div",{class:`${i}-progress-icon`,"aria-hidden":!0},r(L,{clsPrefix:i},{default:()=>V[p]})):r("div",{class:`${i}-progress-text`,style:{color:l},role:"none"},r("span",{class:`${i}-progress-text__percentage`},f),r("span",{class:`${i}-progress-text__unit`},b))):null)}}}),F={success:r(_,null),error:r(q,null),warning:r(O,null),info:r(j,null)},J=P({name:"ProgressLine",props:{clsPrefix:{type:String,required:!0},percentage:{type:Number,default:0},railColor:String,railStyle:[String,Object],fillColor:[String,Object],status:{type:String,required:!0},indicatorPlacement:{type:String,required:!0},indicatorTextColor:String,unit:{type:String,default:"%"},processing:{type:Boolean,required:!0},showIndicator:{type:Boolean,required:!0},height:[String,Number],railBorderRadius:[String,Number],fillBorderRadius:[String,Number]},setup(e,{slots:u}){const c=v(()=>k(e.height)),y=v(()=>{var t,n;return typeof e.fillColor=="object"?`linear-gradient(to right, ${(t=e.fillColor)===null||t===void 0?void 0:t.stops[0]} , ${(n=e.fillColor)===null||n===void 0?void 0:n.stops[1]})`:e.fillColor}),d=v(()=>e.railBorderRadius!==void 0?k(e.railBorderRadius):e.height!==void 0?k(e.height,{c:.5}):""),o=v(()=>e.fillBorderRadius!==void 0?k(e.fillBorderRadius):e.railBorderRadius!==void 0?k(e.railBorderRadius):e.height!==void 0?k(e.height,{c:.5}):"");return()=>{const{indicatorPlacement:t,railColor:n,railStyle:g,percentage:p,unit:f,indicatorTextColor:h,status:l,showIndicator:b,processing:s,clsPrefix:i}=e;return r("div",{class:`${i}-progress-content`,role:"none"},r("div",{class:`${i}-progress-graph`,"aria-hidden":!0},r("div",{class:[`${i}-progress-graph-line`,{[`${i}-progress-graph-line--indicator-${t}`]:!0}]},r("div",{class:`${i}-progress-graph-line-rail`,style:[{backgroundColor:n,height:c.value,borderRadius:d.value},g]},r("div",{class:[`${i}-progress-graph-line-fill`,s&&`${i}-progress-graph-line-fill--processing`],style:{maxWidth:`${e.percentage}%`,background:y.value,height:c.value,lineHeight:c.value,borderRadius:o.value}},t==="inside"?r("div",{class:`${i}-progress-graph-line-indicator`,style:{color:h}},u.default?u.default():`${p}${f}`):null)))),b&&t==="outside"?r("div",null,u.default?r("div",{class:`${i}-progress-custom-content`,style:{color:h},role:"none"},u.default()):l==="default"?r("div",{role:"none",class:`${i}-progress-icon ${i}-progress-icon--as-text`,style:{color:h}},p,f):r("div",{class:`${i}-progress-icon`,"aria-hidden":!0},r(L,{clsPrefix:i},{default:()=>F[l]}))):null)}}});function W(e,u,c=100){return`m ${c/2} ${c/2-e} a ${e} ${e} 0 1 1 0 ${2*e} a ${e} ${e} 0 1 1 0 -${2*e}`}const K=P({name:"ProgressMultipleCircle",props:{clsPrefix:{type:String,required:!0},viewBoxWidth:{type:Number,required:!0},percentage:{type:Array,default:[0]},strokeWidth:{type:Number,required:!0},circleGap:{type:Number,required:!0},showIndicator:{type:Boolean,required:!0},fillColor:{type:Array,default:()=>[]},railColor:{type:Array,default:()=>[]},railStyle:{type:Array,default:()=>[]}},setup(e,{slots:u}){const c=v(()=>e.percentage.map((o,t)=>`${Math.PI*o/100*(e.viewBoxWidth/2-e.strokeWidth/2*(1+2*t)-e.circleGap*t)*2}, ${e.viewBoxWidth*8}`)),y=(d,o)=>{const t=e.fillColor[o],n=typeof t=="object"?t.stops[0]:"",g=typeof t=="object"?t.stops[1]:"";return typeof e.fillColor[o]=="object"&&r("linearGradient",{id:`gradient-${o}`,x1:"100%",y1:"0%",x2:"0%",y2:"100%"},r("stop",{offset:"0%","stop-color":n}),r("stop",{offset:"100%","stop-color":g}))};return()=>{const{viewBoxWidth:d,strokeWidth:o,circleGap:t,showIndicator:n,fillColor:g,railColor:p,railStyle:f,percentage:h,clsPrefix:l}=e;return r("div",{class:`${l}-progress-content`,role:"none"},r("div",{class:`${l}-progress-graph`,"aria-hidden":!0},r("div",{class:`${l}-progress-graph-circle`},r("svg",{viewBox:`0 0 ${d} ${d}`},r("defs",null,h.map((b,s)=>y(b,s))),h.map((b,s)=>r("g",{key:s},r("path",{class:`${l}-progress-graph-circle-rail`,d:W(d/2-o/2*(1+2*s)-t*s,o,d),"stroke-width":o,"stroke-linecap":"round",fill:"none",style:[{strokeDashoffset:0,stroke:p[s]},f[s]]}),r("path",{class:[`${l}-progress-graph-circle-fill`,b===0&&`${l}-progress-graph-circle-fill--empty`],d:W(d/2-o/2*(1+2*s)-t*s,o,d),"stroke-width":o,"stroke-linecap":"round",fill:"none",style:{strokeDasharray:c.value[s],strokeDashoffset:0,stroke:typeof g[s]=="object"?`url(#gradient-${s})`:g[s]}})))))),n&&u.default?r("div",null,r("div",{class:`${l}-progress-text`},u.default())):null)}}}),Q=B([a("progress",{display:"inline-block"},[a("progress-icon",`
 color: var(--n-icon-color);
 transition: color .3s var(--n-bezier);
 `),w("line",`
 width: 100%;
 display: block;
 `,[a("progress-content",`
 display: flex;
 align-items: center;
 `,[a("progress-graph",{flex:1})]),a("progress-custom-content",{marginLeft:"14px"}),a("progress-icon",`
 width: 30px;
 padding-left: 14px;
 height: var(--n-icon-size-line);
 line-height: var(--n-icon-size-line);
 font-size: var(--n-icon-size-line);
 `,[w("as-text",`
 color: var(--n-text-color-line-outer);
 text-align: center;
 width: 40px;
 font-size: var(--n-font-size);
 padding-left: 4px;
 transition: color .3s var(--n-bezier);
 `)])]),w("circle, dashboard",{width:"120px"},[a("progress-custom-content",`
 position: absolute;
 left: 50%;
 top: 50%;
 transform: translateX(-50%) translateY(-50%);
 display: flex;
 align-items: center;
 justify-content: center;
 `),a("progress-text",`
 position: absolute;
 left: 50%;
 top: 50%;
 transform: translateX(-50%) translateY(-50%);
 display: flex;
 align-items: center;
 color: inherit;
 font-size: var(--n-font-size-circle);
 color: var(--n-text-color-circle);
 font-weight: var(--n-font-weight-circle);
 transition: color .3s var(--n-bezier);
 white-space: nowrap;
 `),a("progress-icon",`
 position: absolute;
 left: 50%;
 top: 50%;
 transform: translateX(-50%) translateY(-50%);
 display: flex;
 align-items: center;
 color: var(--n-icon-color);
 font-size: var(--n-icon-size-circle);
 `)]),w("multiple-circle",`
 width: 200px;
 color: inherit;
 `,[a("progress-text",`
 font-weight: var(--n-font-weight-circle);
 color: var(--n-text-color-circle);
 position: absolute;
 left: 50%;
 top: 50%;
 transform: translateX(-50%) translateY(-50%);
 display: flex;
 align-items: center;
 justify-content: center;
 transition: color .3s var(--n-bezier);
 `)]),a("progress-content",{position:"relative"}),a("progress-graph",{position:"relative"},[a("progress-graph-circle",[B("svg",{verticalAlign:"bottom"}),a("progress-graph-circle-fill",`
 stroke: var(--n-fill-color);
 transition:
 opacity .3s var(--n-bezier),
 stroke .3s var(--n-bezier),
 stroke-dasharray .3s var(--n-bezier);
 `,[w("empty",{opacity:0})]),a("progress-graph-circle-rail",`
 transition: stroke .3s var(--n-bezier);
 overflow: hidden;
 stroke: var(--n-rail-color);
 `)]),a("progress-graph-line",[w("indicator-inside",[a("progress-graph-line-rail",`
 height: 16px;
 line-height: 16px;
 border-radius: 10px;
 `,[a("progress-graph-line-fill",`
 height: inherit;
 border-radius: 10px;
 `),a("progress-graph-line-indicator",`
 background: #0000;
 white-space: nowrap;
 text-align: right;
 margin-left: 14px;
 margin-right: 14px;
 height: inherit;
 font-size: 12px;
 color: var(--n-text-color-line-inner);
 transition: color .3s var(--n-bezier);
 `)])]),w("indicator-inside-label",`
 height: 16px;
 display: flex;
 align-items: center;
 `,[a("progress-graph-line-rail",`
 flex: 1;
 transition: background-color .3s var(--n-bezier);
 `),a("progress-graph-line-indicator",`
 background: var(--n-fill-color);
 font-size: 12px;
 transform: translateZ(0);
 display: flex;
 vertical-align: middle;
 height: 16px;
 line-height: 16px;
 padding: 0 10px;
 border-radius: 10px;
 position: absolute;
 white-space: nowrap;
 color: var(--n-text-color-line-inner);
 transition:
 right .2s var(--n-bezier),
 color .3s var(--n-bezier),
 background-color .3s var(--n-bezier);
 `)]),a("progress-graph-line-rail",`
 position: relative;
 overflow: hidden;
 height: var(--n-rail-height);
 border-radius: 5px;
 background-color: var(--n-rail-color);
 transition: background-color .3s var(--n-bezier);
 `,[a("progress-graph-line-fill",`
 background: var(--n-fill-color);
 position: relative;
 border-radius: 5px;
 height: inherit;
 width: 100%;
 max-width: 0%;
 transition:
 background-color .3s var(--n-bezier),
 max-width .2s var(--n-bezier);
 `,[w("processing",[B("&::after",`
 content: "";
 background-image: var(--n-line-bg-processing);
 animation: progress-processing-animation 2s var(--n-bezier) infinite;
 `)])])])])])]),B("@keyframes progress-processing-animation",`
 0% {
 position: absolute;
 left: 0;
 top: 0;
 bottom: 0;
 right: 100%;
 opacity: 1;
 }
 66% {
 position: absolute;
 left: 0;
 top: 0;
 bottom: 0;
 right: 0;
 opacity: 0;
 }
 100% {
 position: absolute;
 left: 0;
 top: 0;
 bottom: 0;
 right: 0;
 opacity: 0;
 }
 `)]),Z=Object.assign(Object.assign({},A.props),{processing:Boolean,type:{type:String,default:"line"},gapDegree:Number,gapOffsetDegree:Number,status:{type:String,default:"default"},railColor:[String,Array],railStyle:[String,Array],color:[String,Array,Object],viewBoxWidth:{type:Number,default:100},strokeWidth:{type:Number,default:7},percentage:[Number,Array],unit:{type:String,default:"%"},showIndicator:{type:Boolean,default:!0},indicatorPosition:{type:String,default:"outside"},indicatorPlacement:{type:String,default:"outside"},indicatorTextColor:String,circleGap:{type:Number,default:1},height:Number,borderRadius:[String,Number],fillBorderRadius:[String,Number],offsetDegree:Number}),re=P({name:"Progress",props:Z,setup(e){const u=v(()=>e.indicatorPlacement||e.indicatorPosition),c=v(()=>{if(e.gapDegree||e.gapDegree===0)return e.gapDegree;if(e.type==="dashboard")return 75}),{mergedClsPrefixRef:y,inlineThemeDisabled:d}=M(e),o=A("Progress","-progress",Q,T,e,y),t=v(()=>{const{status:g}=e,{common:{cubicBezierEaseInOut:p},self:{fontSize:f,fontSizeCircle:h,railColor:l,railHeight:b,iconSizeCircle:s,iconSizeLine:i,textColorCircle:S,textColorLineInner:x,textColorLineOuter:m,lineBgProcessing:$,fontWeightCircle:C,[N("iconColor",g)]:R,[N("fillColor",g)]:z}}=o.value;return{"--n-bezier":p,"--n-fill-color":z,"--n-font-size":f,"--n-font-size-circle":h,"--n-font-weight-circle":C,"--n-icon-color":R,"--n-icon-size-circle":s,"--n-icon-size-line":i,"--n-line-bg-processing":$,"--n-rail-color":l,"--n-rail-height":b,"--n-text-color-circle":S,"--n-text-color-line-inner":x,"--n-text-color-line-outer":m}}),n=d?H("progress",v(()=>e.status[0]),t,e):void 0;return{mergedClsPrefix:y,mergedIndicatorPlacement:u,gapDeg:c,cssVars:d?void 0:t,themeClass:n==null?void 0:n.themeClass,onRender:n==null?void 0:n.onRender}},render(){const{type:e,cssVars:u,indicatorTextColor:c,showIndicator:y,status:d,railColor:o,railStyle:t,color:n,percentage:g,viewBoxWidth:p,strokeWidth:f,mergedIndicatorPlacement:h,unit:l,borderRadius:b,fillBorderRadius:s,height:i,processing:S,circleGap:x,mergedClsPrefix:m,gapDeg:$,gapOffsetDegree:C,themeClass:R,$slots:z,onRender:D}=this;return D==null||D(),r("div",{class:[R,`${m}-progress`,`${m}-progress--${e}`,`${m}-progress--${d}`],style:u,"aria-valuemax":100,"aria-valuemin":0,"aria-valuenow":g,role:e==="circle"||e==="line"||e==="dashboard"?"progressbar":"none"},e==="circle"||e==="dashboard"?r(E,{clsPrefix:m,status:d,showIndicator:y,indicatorTextColor:c,railColor:o,fillColor:n,railStyle:t,offsetDegree:this.offsetDegree,percentage:g,viewBoxWidth:p,strokeWidth:f,gapDegree:$===void 0?e==="dashboard"?75:0:$,gapOffsetDegree:C,unit:l},z):e==="line"?r(J,{clsPrefix:m,status:d,showIndicator:y,indicatorTextColor:c,railColor:o,fillColor:n,railStyle:t,percentage:g,processing:S,indicatorPlacement:h,unit:l,fillBorderRadius:s,railBorderRadius:b,height:i},z):e==="multiple-circle"?r(K,{clsPrefix:m,strokeWidth:f,railColor:o,fillColor:n,railStyle:t,viewBoxWidth:p,percentage:g,showIndicator:y,circleGap:x},z):null)}}),U={xmlns:"http://www.w3.org/2000/svg","xmlns:xlink":"http://www.w3.org/1999/xlink",viewBox:"0 0 24 24"},te=P({name:"Delete24Regular",render:function(u,c){return Y(),X("svg",U,c[0]||(c[0]=[I("g",{fill:"none"},[I("path",{d:"M12 1.75a3.25 3.25 0 0 1 3.245 3.066L15.25 5h5.25a.75.75 0 0 1 .102 1.493L20.5 6.5h-.796l-1.28 13.02a2.75 2.75 0 0 1-2.561 2.474l-.176.006H8.313a2.75 2.75 0 0 1-2.714-2.307l-.023-.174L4.295 6.5H3.5a.75.75 0 0 1-.743-.648L2.75 5.75a.75.75 0 0 1 .648-.743L3.5 5h5.25A3.25 3.25 0 0 1 12 1.75zm6.197 4.75H5.802l1.267 12.872a1.25 1.25 0 0 0 1.117 1.122l.127.006h7.374c.6 0 1.109-.425 1.225-1.002l.02-.126L18.196 6.5zM13.75 9.25a.75.75 0 0 1 .743.648L14.5 10v7a.75.75 0 0 1-1.493.102L13 17v-7a.75.75 0 0 1 .75-.75zm-3.5 0a.75.75 0 0 1 .743.648L11 10v7a.75.75 0 0 1-1.493.102L9.5 17v-7a.75.75 0 0 1 .75-.75zm1.75-6a1.75 1.75 0 0 0-1.744 1.606L10.25 5h3.5A1.75 1.75 0 0 0 12 3.25z",fill:"currentColor"})],-1)]))}});export{te as D,re as _};
