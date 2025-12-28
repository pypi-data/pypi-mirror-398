import{bA as se,d as j,I as s,bs as N,cu as E,r as U,L as M,ct as H,bC as be,af as P,cz as l,bf as u,bh as c,cC as ue,cD as he,bj as S,bk as C,cV as fe,cg as ve,cS as ke,cG as me,bE as ge,c9 as xe,bt as V,eO as pe,bw as Ce,bx as K,by as ye,el as we}from"./index-BwlMlHGj.js";const G=se("n-checkbox-group"),Re={min:Number,max:Number,size:String,value:Array,defaultValue:{type:Array,default:null},disabled:{type:Boolean,default:void 0},"onUpdate:value":[Function,Array],onUpdateValue:[Function,Array],onChange:[Function,Array]},$e=j({name:"CheckboxGroup",props:Re,setup(o){const{mergedClsPrefixRef:i}=N(o),g=E(o),{mergedSizeRef:y,mergedDisabledRef:w}=g,x=U(o.defaultValue),T=M(()=>o.value),h=H(T,x),_=M(()=>{var b;return((b=h.value)===null||b===void 0?void 0:b.length)||0}),r=M(()=>Array.isArray(h.value)?new Set(h.value):new Set);function R(b,n){const{nTriggerFormInput:p,nTriggerFormChange:f}=g,{onChange:a,"onUpdate:value":v,onUpdateValue:k}=o;if(Array.isArray(h.value)){const t=Array.from(h.value),I=t.findIndex(B=>B===n);b?~I||(t.push(n),k&&l(k,t,{actionType:"check",value:n}),v&&l(v,t,{actionType:"check",value:n}),p(),f(),x.value=t,a&&l(a,t)):~I&&(t.splice(I,1),k&&l(k,t,{actionType:"uncheck",value:n}),v&&l(v,t,{actionType:"uncheck",value:n}),a&&l(a,t),x.value=t,p(),f())}else b?(k&&l(k,[n],{actionType:"check",value:n}),v&&l(v,[n],{actionType:"check",value:n}),a&&l(a,[n]),x.value=[n],p(),f()):(k&&l(k,[],{actionType:"uncheck",value:n}),v&&l(v,[],{actionType:"uncheck",value:n}),a&&l(a,[]),x.value=[],p(),f())}return be(G,{checkedCountRef:_,maxRef:P(o,"max"),minRef:P(o,"min"),valueSetRef:r,disabledRef:w,mergedSizeRef:y,toggleCheckbox:R}),{mergedClsPrefix:i}},render(){return s("div",{class:`${this.mergedClsPrefix}-checkbox-group`,role:"group"},this.$slots)}}),ze=()=>s("svg",{viewBox:"0 0 64 64",class:"check-icon"},s("path",{d:"M50.42,16.76L22.34,39.45l-8.1-11.46c-1.12-1.58-3.3-1.96-4.88-0.84c-1.58,1.12-1.95,3.3-0.84,4.88l10.26,14.51  c0.56,0.79,1.42,1.31,2.38,1.45c0.16,0.02,0.32,0.03,0.48,0.03c0.8,0,1.57-0.27,2.2-0.78l30.99-25.03c1.5-1.21,1.74-3.42,0.52-4.92  C54.13,15.78,51.93,15.55,50.42,16.76z"})),Se=()=>s("svg",{viewBox:"0 0 100 100",class:"line-icon"},s("path",{d:"M80.2,55.5H21.4c-2.8,0-5.1-2.5-5.1-5.5l0,0c0-3,2.3-5.5,5.1-5.5h58.7c2.8,0,5.1,2.5,5.1,5.5l0,0C85.2,53.1,82.9,55.5,80.2,55.5z"})),Te=u([c("checkbox",`
 font-size: var(--n-font-size);
 outline: none;
 cursor: pointer;
 display: inline-flex;
 flex-wrap: nowrap;
 align-items: flex-start;
 word-break: break-word;
 line-height: var(--n-size);
 --n-merged-color-table: var(--n-color-table);
 `,[S("show-label","line-height: var(--n-label-line-height);"),u("&:hover",[c("checkbox-box",[C("border","border: var(--n-border-checked);")])]),u("&:focus:not(:active)",[c("checkbox-box",[C("border",`
 border: var(--n-border-focus);
 box-shadow: var(--n-box-shadow-focus);
 `)])]),S("inside-table",[c("checkbox-box",`
 background-color: var(--n-merged-color-table);
 `)]),S("checked",[c("checkbox-box",`
 background-color: var(--n-color-checked);
 `,[c("checkbox-icon",[u(".check-icon",`
 opacity: 1;
 transform: scale(1);
 `)])])]),S("indeterminate",[c("checkbox-box",[c("checkbox-icon",[u(".check-icon",`
 opacity: 0;
 transform: scale(.5);
 `),u(".line-icon",`
 opacity: 1;
 transform: scale(1);
 `)])])]),S("checked, indeterminate",[u("&:focus:not(:active)",[c("checkbox-box",[C("border",`
 border: var(--n-border-checked);
 box-shadow: var(--n-box-shadow-focus);
 `)])]),c("checkbox-box",`
 background-color: var(--n-color-checked);
 border-left: 0;
 border-top: 0;
 `,[C("border",{border:"var(--n-border-checked)"})])]),S("disabled",{cursor:"not-allowed"},[S("checked",[c("checkbox-box",`
 background-color: var(--n-color-disabled-checked);
 `,[C("border",{border:"var(--n-border-disabled-checked)"}),c("checkbox-icon",[u(".check-icon, .line-icon",{fill:"var(--n-check-mark-color-disabled-checked)"})])])]),c("checkbox-box",`
 background-color: var(--n-color-disabled);
 `,[C("border",`
 border: var(--n-border-disabled);
 `),c("checkbox-icon",[u(".check-icon, .line-icon",`
 fill: var(--n-check-mark-color-disabled);
 `)])]),C("label",`
 color: var(--n-text-color-disabled);
 `)]),c("checkbox-box-wrapper",`
 position: relative;
 width: var(--n-size);
 flex-shrink: 0;
 flex-grow: 0;
 user-select: none;
 -webkit-user-select: none;
 `),c("checkbox-box",`
 position: absolute;
 left: 0;
 top: 50%;
 transform: translateY(-50%);
 height: var(--n-size);
 width: var(--n-size);
 display: inline-block;
 box-sizing: border-box;
 border-radius: var(--n-border-radius);
 background-color: var(--n-color);
 transition: background-color 0.3s var(--n-bezier);
 `,[C("border",`
 transition:
 border-color .3s var(--n-bezier),
 box-shadow .3s var(--n-bezier);
 border-radius: inherit;
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 border: var(--n-border);
 `),c("checkbox-icon",`
 display: flex;
 align-items: center;
 justify-content: center;
 position: absolute;
 left: 1px;
 right: 1px;
 top: 1px;
 bottom: 1px;
 `,[u(".check-icon, .line-icon",`
 width: 100%;
 fill: var(--n-check-mark-color);
 opacity: 0;
 transform: scale(0.5);
 transform-origin: center;
 transition:
 fill 0.3s var(--n-bezier),
 transform 0.3s var(--n-bezier),
 opacity 0.3s var(--n-bezier),
 border-color 0.3s var(--n-bezier);
 `),fe({left:"1px",top:"1px"})])]),C("label",`
 color: var(--n-text-color);
 transition: color .3s var(--n-bezier);
 user-select: none;
 -webkit-user-select: none;
 padding: var(--n-label-padding);
 font-weight: var(--n-label-font-weight);
 `,[u("&:empty",{display:"none"})])]),ue(c("checkbox",`
 --n-merged-color-table: var(--n-color-table-modal);
 `)),he(c("checkbox",`
 --n-merged-color-table: var(--n-color-table-popover);
 `))]),_e=Object.assign(Object.assign({},V.props),{size:String,checked:{type:[Boolean,String,Number],default:void 0},defaultChecked:{type:[Boolean,String,Number],default:!1},value:[String,Number],disabled:{type:Boolean,default:void 0},indeterminate:Boolean,label:String,focusable:{type:Boolean,default:!0},checkedValue:{type:[Boolean,String,Number],default:!0},uncheckedValue:{type:[Boolean,String,Number],default:!1},"onUpdate:checked":[Function,Array],onUpdateChecked:[Function,Array],privateInsideTable:Boolean,onChange:[Function,Array]}),Ae=j({name:"Checkbox",props:_e,setup(o){const i=ge(G,null),g=U(null),{mergedClsPrefixRef:y,inlineThemeDisabled:w,mergedRtlRef:x}=N(o),T=U(o.defaultChecked),h=P(o,"checked"),_=H(h,T),r=xe(()=>{if(i){const e=i.valueSetRef.value;return e&&o.value!==void 0?e.has(o.value):!1}else return _.value===o.checkedValue}),R=E(o,{mergedSize(e){const{size:m}=o;if(m!==void 0)return m;if(i){const{value:d}=i.mergedSizeRef;if(d!==void 0)return d}if(e){const{mergedSize:d}=e;if(d!==void 0)return d.value}return"medium"},mergedDisabled(e){const{disabled:m}=o;if(m!==void 0)return m;if(i){if(i.disabledRef.value)return!0;const{maxRef:{value:d},checkedCountRef:z}=i;if(d!==void 0&&z.value>=d&&!r.value)return!0;const{minRef:{value:$}}=i;if($!==void 0&&z.value<=$&&r.value)return!0}return e?e.disabled.value:!1}}),{mergedDisabledRef:b,mergedSizeRef:n}=R,p=V("Checkbox","-checkbox",Te,pe,o,y);function f(e){if(i&&o.value!==void 0)i.toggleCheckbox(!r.value,o.value);else{const{onChange:m,"onUpdate:checked":d,onUpdateChecked:z}=o,{nTriggerFormInput:$,nTriggerFormChange:F}=R,A=r.value?o.uncheckedValue:o.checkedValue;d&&l(d,A,e),z&&l(z,A,e),m&&l(m,A,e),$(),F(),T.value=A}}function a(e){b.value||f(e)}function v(e){if(!b.value)switch(e.key){case" ":case"Enter":f(e)}}function k(e){switch(e.key){case" ":e.preventDefault()}}const t={focus:()=>{var e;(e=g.value)===null||e===void 0||e.focus()},blur:()=>{var e;(e=g.value)===null||e===void 0||e.blur()}},I=Ce("Checkbox",x,y),B=M(()=>{const{value:e}=n,{common:{cubicBezierEaseInOut:m},self:{borderRadius:d,color:z,colorChecked:$,colorDisabled:F,colorTableHeader:A,colorTableHeaderModal:L,colorTableHeaderPopover:O,checkMarkColor:W,checkMarkColorDisabled:Y,border:q,borderFocus:J,borderDisabled:Q,borderChecked:X,boxShadowFocus:Z,textColor:ee,textColorDisabled:oe,checkMarkColorDisabledChecked:re,colorDisabledChecked:ne,borderDisabledChecked:ce,labelPadding:ae,labelLineHeight:le,labelFontWeight:ie,[K("fontSize",e)]:te,[K("size",e)]:de}}=p.value;return{"--n-label-line-height":le,"--n-label-font-weight":ie,"--n-size":de,"--n-bezier":m,"--n-border-radius":d,"--n-border":q,"--n-border-checked":X,"--n-border-focus":J,"--n-border-disabled":Q,"--n-border-disabled-checked":ce,"--n-box-shadow-focus":Z,"--n-color":z,"--n-color-checked":$,"--n-color-table":A,"--n-color-table-modal":L,"--n-color-table-popover":O,"--n-color-disabled":F,"--n-color-disabled-checked":ne,"--n-text-color":ee,"--n-text-color-disabled":oe,"--n-check-mark-color":W,"--n-check-mark-color-disabled":Y,"--n-check-mark-color-disabled-checked":re,"--n-font-size":te,"--n-label-padding":ae}}),D=w?ye("checkbox",M(()=>n.value[0]),B,o):void 0;return Object.assign(R,t,{rtlEnabled:I,selfRef:g,mergedClsPrefix:y,mergedDisabled:b,renderedChecked:r,mergedTheme:p,labelId:we(),handleClick:a,handleKeyUp:v,handleKeyDown:k,cssVars:w?void 0:B,themeClass:D==null?void 0:D.themeClass,onRender:D==null?void 0:D.onRender})},render(){var o;const{$slots:i,renderedChecked:g,mergedDisabled:y,indeterminate:w,privateInsideTable:x,cssVars:T,labelId:h,label:_,mergedClsPrefix:r,focusable:R,handleKeyUp:b,handleKeyDown:n,handleClick:p}=this;(o=this.onRender)===null||o===void 0||o.call(this);const f=ve(i.default,a=>_||a?s("span",{class:`${r}-checkbox__label`,id:h},_||a):null);return s("div",{ref:"selfRef",class:[`${r}-checkbox`,this.themeClass,this.rtlEnabled&&`${r}-checkbox--rtl`,g&&`${r}-checkbox--checked`,y&&`${r}-checkbox--disabled`,w&&`${r}-checkbox--indeterminate`,x&&`${r}-checkbox--inside-table`,f&&`${r}-checkbox--show-label`],tabindex:y||!R?void 0:0,role:"checkbox","aria-checked":w?"mixed":g,"aria-labelledby":h,style:T,onKeyup:b,onKeydown:n,onClick:p,onMousedown:()=>{me("selectstart",window,a=>{a.preventDefault()},{once:!0})}},s("div",{class:`${r}-checkbox-box-wrapper`}," ",s("div",{class:`${r}-checkbox-box`},s(ke,null,{default:()=>this.indeterminate?s("div",{key:"indeterminate",class:`${r}-checkbox-icon`},Se()):s("div",{key:"check",class:`${r}-checkbox-icon`},ze())}),s("div",{class:`${r}-checkbox-box__border`}))),f)}});export{Ae as _,$e as a};
