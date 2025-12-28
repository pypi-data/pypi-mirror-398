import{d as z,r as h,L as v,a3 as k,E as B,af as S,I as s,bf as r,bg as A,bh as f,bi as I,bj as c,bk as _,bl as M,bm as W,bn as F,bo as C,bp as X,bq as q,b3 as D,br as L,bs as V,bt as Y,bu as j,bv as U,o as Z,bw as G,bx as H,by as K,bz as J}from"./index-BwlMlHGj.js";const O=z({name:"SlotMachineNumber",props:{clsPrefix:{type:String,required:!0},value:{type:[Number,String],required:!0},oldOriginalNumber:{type:Number,default:void 0},newOriginalNumber:{type:Number,default:void 0}},setup(e){const o=h(null),i=h(e.value),u=h(e.value),t=h("up"),a=h(!1),m=v(()=>a.value?`${e.clsPrefix}-base-slot-machine-current-number--${t.value}-scroll`:null),g=v(()=>a.value?`${e.clsPrefix}-base-slot-machine-old-number--${t.value}-scroll`:null);k(S(e,"value"),(n,l)=>{i.value=l,u.value=n,B(N)});function N(){const n=e.newOriginalNumber,l=e.oldOriginalNumber;l===void 0||n===void 0||(n>l?w("up"):l>n&&w("down"))}function w(n){t.value=n,a.value=!1,B(()=>{var l;(l=o.value)===null||l===void 0||l.offsetWidth,a.value=!0})}return()=>{const{clsPrefix:n}=e;return s("span",{ref:o,class:`${n}-base-slot-machine-number`},i.value!==null?s("span",{class:[`${n}-base-slot-machine-old-number ${n}-base-slot-machine-old-number--top`,g.value]},i.value):null,s("span",{class:[`${n}-base-slot-machine-current-number`,m.value]},s("span",{ref:"numberWrapper",class:[`${n}-base-slot-machine-current-number__inner`,typeof e.value!="number"&&`${n}-base-slot-machine-current-number__inner--not-number`]},u.value)),i.value!==null?s("span",{class:[`${n}-base-slot-machine-old-number ${n}-base-slot-machine-old-number--bottom`,g.value]},i.value):null)}}}),{cubicBezierEaseOut:x}=A;function Q({duration:e=".2s"}={}){return[r("&.fade-up-width-expand-transition-leave-active",{transition:`
 opacity ${e} ${x},
 max-width ${e} ${x},
 transform ${e} ${x}
 `}),r("&.fade-up-width-expand-transition-enter-active",{transition:`
 opacity ${e} ${x},
 max-width ${e} ${x},
 transform ${e} ${x}
 `}),r("&.fade-up-width-expand-transition-enter-to",{opacity:1,transform:"translateX(0) translateY(0)"}),r("&.fade-up-width-expand-transition-enter-from",{maxWidth:"0 !important",opacity:0,transform:"translateY(60%)"}),r("&.fade-up-width-expand-transition-leave-from",{opacity:1,transform:"translateY(0)"}),r("&.fade-up-width-expand-transition-leave-to",{maxWidth:"0 !important",opacity:0,transform:"translateY(60%)"})]}const ee=r([r("@keyframes n-base-slot-machine-fade-up-in",`
 from {
 transform: translateY(60%);
 opacity: 0;
 }
 to {
 transform: translateY(0);
 opacity: 1;
 }
 `),r("@keyframes n-base-slot-machine-fade-down-in",`
 from {
 transform: translateY(-60%);
 opacity: 0;
 }
 to {
 transform: translateY(0);
 opacity: 1;
 }
 `),r("@keyframes n-base-slot-machine-fade-up-out",`
 from {
 transform: translateY(0%);
 opacity: 1;
 }
 to {
 transform: translateY(-60%);
 opacity: 0;
 }
 `),r("@keyframes n-base-slot-machine-fade-down-out",`
 from {
 transform: translateY(0%);
 opacity: 1;
 }
 to {
 transform: translateY(60%);
 opacity: 0;
 }
 `),f("base-slot-machine",`
 overflow: hidden;
 white-space: nowrap;
 display: inline-block;
 height: 18px;
 line-height: 18px;
 `,[f("base-slot-machine-number",`
 display: inline-block;
 position: relative;
 height: 18px;
 width: .6em;
 max-width: .6em;
 `,[Q({duration:".2s"}),I({duration:".2s",delay:"0s"}),f("base-slot-machine-old-number",`
 display: inline-block;
 opacity: 0;
 position: absolute;
 left: 0;
 right: 0;
 `,[c("top",{transform:"translateY(-100%)"}),c("bottom",{transform:"translateY(100%)"}),c("down-scroll",{animation:"n-base-slot-machine-fade-down-out .2s cubic-bezier(0, 0, .2, 1)",animationIterationCount:1}),c("up-scroll",{animation:"n-base-slot-machine-fade-up-out .2s cubic-bezier(0, 0, .2, 1)",animationIterationCount:1})]),f("base-slot-machine-current-number",`
 display: inline-block;
 position: absolute;
 left: 0;
 top: 0;
 bottom: 0;
 right: 0;
 opacity: 1;
 transform: translateY(0);
 width: .6em;
 `,[c("down-scroll",{animation:"n-base-slot-machine-fade-down-in .2s cubic-bezier(0, 0, .2, 1)",animationIterationCount:1}),c("up-scroll",{animation:"n-base-slot-machine-fade-up-in .2s cubic-bezier(0, 0, .2, 1)",animationIterationCount:1}),_("inner",`
 display: inline-block;
 position: absolute;
 right: 0;
 top: 0;
 width: .6em;
 `,[c("not-number",`
 right: unset;
 left: 0;
 `)])])])])]),ae=z({name:"BaseSlotMachine",props:{clsPrefix:{type:String,required:!0},value:{type:[Number,String],default:0},max:{type:Number,default:void 0},appeared:{type:Boolean,required:!0}},setup(e){M("-base-slot-machine",ee,S(e,"clsPrefix"));const o=h(),i=h(),u=v(()=>{if(typeof e.value=="string")return[];if(e.value<1)return[0];const t=[];let a=e.value;for(e.max!==void 0&&(a=Math.min(e.max,a));a>=1;)t.push(a%10),a/=10,a=Math.floor(a);return t.reverse(),t});return k(S(e,"value"),(t,a)=>{typeof t=="string"?(i.value=void 0,o.value=void 0):typeof a=="string"?(i.value=t,o.value=void 0):(i.value=t,o.value=a)}),()=>{const{value:t,clsPrefix:a}=e;return typeof t=="number"?s("span",{class:`${a}-base-slot-machine`},s(W,{name:"fade-up-width-expand-transition",tag:"span"},{default:()=>u.value.map((m,g)=>s(O,{clsPrefix:a,key:u.value.length-g-1,oldOriginalNumber:o.value,newOriginalNumber:i.value,value:m}))}),s(F,{key:"+",width:!0},{default:()=>e.max!==void 0&&e.max<t?s(O,{clsPrefix:a,value:"+"}):null})):s("span",{class:`${a}-base-slot-machine`},t)}}}),te=r([r("@keyframes badge-wave-spread",{from:{boxShadow:"0 0 0.5px 0px var(--n-ripple-color)",opacity:.6},to:{boxShadow:"0 0 0.5px 4.5px var(--n-ripple-color)",opacity:0}}),f("badge",`
 display: inline-flex;
 position: relative;
 vertical-align: middle;
 font-family: var(--n-font-family);
 `,[c("as-is",[f("badge-sup",{position:"static",transform:"translateX(0)"},[C({transformOrigin:"left bottom",originalTransform:"translateX(0)"})])]),c("dot",[f("badge-sup",`
 height: 8px;
 width: 8px;
 padding: 0;
 min-width: 8px;
 left: 100%;
 bottom: calc(100% - 4px);
 `,[r("::before","border-radius: 4px;")])]),f("badge-sup",`
 background: var(--n-color);
 transition:
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier);
 color: #FFF;
 position: absolute;
 height: 18px;
 line-height: 18px;
 border-radius: 9px;
 padding: 0 6px;
 text-align: center;
 font-size: var(--n-font-size);
 transform: translateX(-50%);
 left: 100%;
 bottom: calc(100% - 9px);
 font-variant-numeric: tabular-nums;
 z-index: 2;
 display: flex;
 align-items: center;
 `,[C({transformOrigin:"left bottom",originalTransform:"translateX(-50%)"}),f("base-wave",{zIndex:1,animationDuration:"2s",animationIterationCount:"infinite",animationDelay:"1s",animationTimingFunction:"var(--n-ripple-bezier)",animationName:"badge-wave-spread"}),r("&::before",`
 opacity: 0;
 transform: scale(1);
 border-radius: 9px;
 content: "";
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 `)])])]),ne=Object.assign(Object.assign({},Y.props),{value:[String,Number],max:Number,dot:Boolean,type:{type:String,default:"default"},show:{type:Boolean,default:!0},showZero:Boolean,processing:Boolean,color:String,offset:Array}),oe=z({name:"Badge",props:ne,setup(e,{slots:o}){const{mergedClsPrefixRef:i,inlineThemeDisabled:u,mergedRtlRef:t}=V(e),a=Y("Badge","-badge",te,j,e,i),m=h(!1),g=()=>{m.value=!0},N=()=>{m.value=!1},w=v(()=>e.show&&(e.dot||e.value!==void 0&&!(!e.showZero&&Number(e.value)<=0)||!U(o.value)));Z(()=>{w.value&&(m.value=!0)});const n=G("Badge",t,i),l=v(()=>{const{type:b,color:d}=e,{common:{cubicBezierEaseInOut:p,cubicBezierEaseOut:R},self:{[H("color",b)]:$,fontFamily:P,fontSize:T}}=a.value;return{"--n-font-size":T,"--n-font-family":P,"--n-color":d||$,"--n-ripple-color":d||$,"--n-bezier":p,"--n-ripple-bezier":R}}),y=u?K("badge",v(()=>{let b="";const{type:d,color:p}=e;return d&&(b+=d[0]),p&&(b+=J(p)),b}),l,e):void 0,E=v(()=>{const{offset:b}=e;if(!b)return;const[d,p]=b,R=typeof d=="number"?`${d}px`:d,$=typeof p=="number"?`${p}px`:p;return{transform:`translate(calc(${n!=null&&n.value?"50%":"-50%"} + ${R}), ${$})`}});return{rtlEnabled:n,mergedClsPrefix:i,appeared:m,showBadge:w,handleAfterEnter:g,handleAfterLeave:N,cssVars:u?void 0:l,themeClass:y==null?void 0:y.themeClass,onRender:y==null?void 0:y.onRender,offsetStyle:E}},render(){var e;const{mergedClsPrefix:o,onRender:i,themeClass:u,$slots:t}=this;i==null||i();const a=(e=t.default)===null||e===void 0?void 0:e.call(t);return s("div",{class:[`${o}-badge`,this.rtlEnabled&&`${o}-badge--rtl`,u,{[`${o}-badge--dot`]:this.dot,[`${o}-badge--as-is`]:!a}],style:this.cssVars},a,s(X,{name:"fade-in-scale-up-transition",onAfterEnter:this.handleAfterEnter,onAfterLeave:this.handleAfterLeave},{default:()=>this.showBadge?s("sup",{class:`${o}-badge-sup`,title:q(this.value),style:this.offsetStyle},D(t.value,()=>[this.dot?null:s(ae,{clsPrefix:o,appeared:this.appeared,max:this.max,value:this.value})]),this.processing?s(L,{clsPrefix:o}):null):null}))}});export{oe as _};
