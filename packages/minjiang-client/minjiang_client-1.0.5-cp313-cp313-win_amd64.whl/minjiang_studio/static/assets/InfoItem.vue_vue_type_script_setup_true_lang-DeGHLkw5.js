import{bh as c,bf as s,bk as v,bj as $,bA as A,d as b,I as h,bs as I,bt as k,bB as P,bC as T,af as V,L as x,by as j,r as E,o as S,bd as D,bD as M,bE as O,b3 as F,e as C,f as _,h as d,A as K,a7 as N,l as U,ai as w}from"./index-BwlMlHGj.js";const q=c("breadcrumb",`
 white-space: nowrap;
 cursor: default;
 line-height: var(--n-item-line-height);
`,[s("ul",`
 list-style: none;
 padding: 0;
 margin: 0;
 `),s("a",`
 color: inherit;
 text-decoration: inherit;
 `),c("breadcrumb-item",`
 font-size: var(--n-font-size);
 transition: color .3s var(--n-bezier);
 display: inline-flex;
 align-items: center;
 `,[c("icon",`
 font-size: 18px;
 vertical-align: -.2em;
 transition: color .3s var(--n-bezier);
 color: var(--n-item-text-color);
 `),s("&:not(:last-child)",[$("clickable",[v("link",`
 cursor: pointer;
 `,[s("&:hover",`
 background-color: var(--n-item-color-hover);
 `),s("&:active",`
 background-color: var(--n-item-color-pressed); 
 `)])])]),v("link",`
 padding: 4px;
 border-radius: var(--n-item-border-radius);
 transition:
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier);
 color: var(--n-item-text-color);
 position: relative;
 `,[s("&:hover",`
 color: var(--n-item-text-color-hover);
 `,[c("icon",`
 color: var(--n-item-text-color-hover);
 `)]),s("&:active",`
 color: var(--n-item-text-color-pressed);
 `,[c("icon",`
 color: var(--n-item-text-color-pressed);
 `)])]),v("separator",`
 margin: 0 8px;
 color: var(--n-separator-color);
 transition: color .3s var(--n-bezier);
 user-select: none;
 -webkit-user-select: none;
 `),s("&:last-child",[v("link",`
 font-weight: var(--n-font-weight-active);
 cursor: unset;
 color: var(--n-item-text-color-active);
 `,[c("icon",`
 color: var(--n-item-text-color-active);
 `)]),v("separator",`
 display: none;
 `)])])]),z=A("n-breadcrumb"),G=Object.assign(Object.assign({},k.props),{separator:{type:String,default:"/"}}),re=b({name:"Breadcrumb",props:G,setup(e){const{mergedClsPrefixRef:t,inlineThemeDisabled:r}=I(e),n=k("Breadcrumb","-breadcrumb",q,P,e,t);T(z,{separatorRef:V(e,"separator"),mergedClsPrefixRef:t});const l=x(()=>{const{common:{cubicBezierEaseInOut:u},self:{separatorColor:m,itemTextColor:a,itemTextColorHover:i,itemTextColorPressed:f,itemTextColorActive:p,fontSize:g,fontWeightActive:B,itemBorderRadius:y,itemColorHover:R,itemColorPressed:L,itemLineHeight:H}}=n.value;return{"--n-font-size":g,"--n-bezier":u,"--n-item-text-color":a,"--n-item-text-color-hover":i,"--n-item-text-color-pressed":f,"--n-item-text-color-active":p,"--n-separator-color":m,"--n-item-color-hover":R,"--n-item-color-pressed":L,"--n-item-border-radius":y,"--n-font-weight-active":B,"--n-item-line-height":H}}),o=r?j("breadcrumb",void 0,l,e):void 0;return{mergedClsPrefix:t,cssVars:r?void 0:l,themeClass:o==null?void 0:o.themeClass,onRender:o==null?void 0:o.onRender}},render(){var e;return(e=this.onRender)===null||e===void 0||e.call(this),h("nav",{class:[`${this.mergedClsPrefix}-breadcrumb`,this.themeClass],style:this.cssVars,"aria-label":"Breadcrumb"},h("ul",null,this.$slots))}});function J(e=M?window:null){const t=()=>{const{hash:l,host:o,hostname:u,href:m,origin:a,pathname:i,port:f,protocol:p,search:g}=(e==null?void 0:e.location)||{};return{hash:l,host:o,hostname:u,href:m,origin:a,pathname:i,port:f,protocol:p,search:g}},r=E(t()),n=()=>{r.value=t()};return S(()=>{e&&(e.addEventListener("popstate",n),e.addEventListener("hashchange",n))}),D(()=>{e&&(e.removeEventListener("popstate",n),e.removeEventListener("hashchange",n))}),r}const Q={separator:String,href:String,clickable:{type:Boolean,default:!0},onClick:Function},te=b({name:"BreadcrumbItem",props:Q,slots:Object,setup(e,{slots:t}){const r=O(z,null);if(!r)return()=>null;const{separatorRef:n,mergedClsPrefixRef:l}=r,o=J(),u=x(()=>e.href?"a":"span"),m=x(()=>o.value.href===e.href?"location":null);return()=>{const{value:a}=l;return h("li",{class:[`${a}-breadcrumb-item`,e.clickable&&`${a}-breadcrumb-item--clickable`]},h(u.value,{class:`${a}-breadcrumb-item__link`,"aria-current":m.value,href:e.href,onClick:e.onClick},t),h("span",{class:`${a}-breadcrumb-item__separator`,"aria-hidden":"true"},F(t.separator,()=>{var i;return[(i=e.separator)!==null&&i!==void 0?i:n.value]})))}}}),X={xmlns:"http://www.w3.org/2000/svg","xmlns:xlink":"http://www.w3.org/1999/xlink",viewBox:"0 0 512 512"},oe=b({name:"Duplicate",render:function(t,r){return _(),C("svg",X,r[0]||(r[0]=[d("path",{d:"M408 112H184a72 72 0 0 0-72 72v224a72 72 0 0 0 72 72h224a72 72 0 0 0 72-72V184a72 72 0 0 0-72-72zm-32.45 200H312v63.55c0 8.61-6.62 16-15.23 16.43A16 16 0 0 1 280 376v-64h-63.55c-8.61 0-16-6.62-16.43-15.23A16 16 0 0 1 216 280h64v-63.55c0-8.61 6.62-16 15.23-16.43A16 16 0 0 1 312 216v64h64a16 16 0 0 1 16 16.77c-.42 8.61-7.84 15.23-16.45 15.23z",fill:"currentColor"},null,-1),d("path",{d:"M395.88 80A72.12 72.12 0 0 0 328 32H104a72 72 0 0 0-72 72v224a72.12 72.12 0 0 0 48 67.88V160a80 80 0 0 1 80-80z",fill:"currentColor"},null,-1)]))}}),Y={xmlns:"http://www.w3.org/2000/svg","xmlns:xlink":"http://www.w3.org/1999/xlink",viewBox:"0 0 24 24"},ne=b({name:"Home24Filled",render:function(t,r){return _(),C("svg",Y,r[0]||(r[0]=[d("g",{fill:"none"},[d("path",{d:"M10.55 2.533a2.25 2.25 0 0 1 2.9 0l6.75 5.695c.508.427.8 1.056.8 1.72v9.802a1.75 1.75 0 0 1-1.75 1.75h-3a1.75 1.75 0 0 1-1.75-1.75v-5a.75.75 0 0 0-.75-.75h-3.5a.75.75 0 0 0-.75.75v5a1.75 1.75 0 0 1-1.75 1.75h-3A1.75 1.75 0 0 1 3 19.75V9.947c0-.663.292-1.292.8-1.72l6.75-5.694z",fill:"currentColor"})],-1)]))}}),Z={class:"text-xs opacity-70"},W={class:"text-xs"},ae=b({__name:"InfoItem",setup(e){const t=K();return(r,n)=>(_(),C("div",{class:"flex justify-between items-center py-2 border-b",style:N({borderColor:U(t).dividerColor})},[d("div",Z,[w(r.$slots,"label")]),d("div",W,[w(r.$slots,"default")])],4))}});export{oe as D,ne as H,re as _,te as a,ae as b};
