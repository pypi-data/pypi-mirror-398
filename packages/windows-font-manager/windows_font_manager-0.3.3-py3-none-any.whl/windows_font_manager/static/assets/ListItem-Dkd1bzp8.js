import{L as v,a0 as c,N as t,a1 as R,M as f,d as M,a3 as T,q as a,b as ve,T as S,U as B,bL as ge,p as D,A as E,a6 as L,m as I,X as s,a9 as ue,Y as N,bI as H,aq as fe,aj as F,ar as me,as as pe,bM as Ce,n as ke,bg as xe}from"./index-AF5o79Y5.js";import{N as ze}from"./Close-BJWDkOCE.js";const $e={color:Object,type:{type:String,default:"default"},round:Boolean,size:{type:String,default:"medium"},closable:Boolean,disabled:{type:Boolean,default:void 0}},ye=v("tag",`
 --n-close-margin: var(--n-close-margin-top) var(--n-close-margin-right) var(--n-close-margin-bottom) var(--n-close-margin-left);
 white-space: nowrap;
 position: relative;
 box-sizing: border-box;
 cursor: default;
 display: inline-flex;
 align-items: center;
 flex-wrap: nowrap;
 padding: var(--n-padding);
 border-radius: var(--n-border-radius);
 color: var(--n-text-color);
 background-color: var(--n-color);
 transition: 
 border-color .3s var(--n-bezier),
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier),
 box-shadow .3s var(--n-bezier),
 opacity .3s var(--n-bezier);
 line-height: 1;
 height: var(--n-height);
 font-size: var(--n-font-size);
`,[c("strong",`
 font-weight: var(--n-font-weight-strong);
 `),t("border",`
 pointer-events: none;
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 border-radius: inherit;
 border: var(--n-border);
 transition: border-color .3s var(--n-bezier);
 `),t("icon",`
 display: flex;
 margin: 0 4px 0 0;
 color: var(--n-text-color);
 transition: color .3s var(--n-bezier);
 font-size: var(--n-avatar-size-override);
 `),t("avatar",`
 display: flex;
 margin: 0 6px 0 0;
 `),t("close",`
 margin: var(--n-close-margin);
 transition:
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier);
 `),c("round",`
 padding: 0 calc(var(--n-height) / 3);
 border-radius: calc(var(--n-height) / 2);
 `,[t("icon",`
 margin: 0 4px 0 calc((var(--n-height) - 8px) / -2);
 `),t("avatar",`
 margin: 0 6px 0 calc((var(--n-height) - 8px) / -2);
 `),c("closable",`
 padding: 0 calc(var(--n-height) / 4) 0 calc(var(--n-height) / 3);
 `)]),c("icon, avatar",[c("round",`
 padding: 0 calc(var(--n-height) / 3) 0 calc(var(--n-height) / 2);
 `)]),c("disabled",`
 cursor: not-allowed !important;
 opacity: var(--n-opacity-disabled);
 `),c("checkable",`
 cursor: pointer;
 box-shadow: none;
 color: var(--n-text-color-checkable);
 background-color: var(--n-color-checkable);
 `,[R("disabled",[f("&:hover","background-color: var(--n-color-hover-checkable);",[R("checked","color: var(--n-text-color-hover-checkable);")]),f("&:active","background-color: var(--n-color-pressed-checkable);",[R("checked","color: var(--n-text-color-pressed-checkable);")])]),c("checked",`
 color: var(--n-text-color-checked);
 background-color: var(--n-color-checked);
 `,[R("disabled",[f("&:hover","background-color: var(--n-color-checked-hover);"),f("&:active","background-color: var(--n-color-checked-pressed);")])])])]),Re=Object.assign(Object.assign(Object.assign({},B.props),$e),{bordered:{type:Boolean,default:void 0},checked:Boolean,checkable:Boolean,strong:Boolean,triggerClickOnClose:Boolean,onClose:[Array,Function],onMouseenter:Function,onMouseleave:Function,"onUpdate:checked":Function,onUpdateChecked:Function,internalCloseFocusable:{type:Boolean,default:!0},internalCloseIsButtonTag:{type:Boolean,default:!0},onCheckedChange:Function}),Be=F("n-tag"),Me=M({name:"Tag",props:Re,slots:Object,setup(e){const l=ve(null),{mergedBorderedRef:o,mergedClsPrefixRef:d,inlineThemeDisabled:m,mergedRtlRef:$}=S(e),p=B("Tag","-tag",ye,ge,e,d);D(Be,{roundRef:E(e,"round")});function i(){if(!e.disabled&&e.checkable){const{checked:r,onCheckedChange:n,onUpdateChecked:u,"onUpdate:checked":b}=e;u&&u(!r),b&&b(!r),n&&n(!r)}}function C(r){if(e.triggerClickOnClose||r.stopPropagation(),!e.disabled){const{onClose:n}=e;n&&fe(n,r)}}const k={setTextContent(r){const{value:n}=l;n&&(n.textContent=r)}},x=L("Tag",$,d),h=I(()=>{const{type:r,size:n,color:{color:u,textColor:b}={}}=e,{common:{cubicBezierEaseInOut:z},self:{padding:P,closeMargin:_,borderRadius:w,opacityDisabled:V,textColorCheckable:K,textColorHoverCheckable:q,textColorPressedCheckable:A,textColorChecked:W,colorCheckable:X,colorHoverCheckable:Y,colorPressedCheckable:G,colorChecked:J,colorCheckedHover:Q,colorCheckedPressed:Z,closeBorderRadius:ee,fontWeightStrong:oe,[s("colorBordered",r)]:re,[s("closeSize",n)]:le,[s("closeIconSize",n)]:ne,[s("fontSize",n)]:te,[s("height",n)]:j,[s("color",r)]:ae,[s("textColor",r)]:se,[s("border",r)]:ce,[s("closeIconColor",r)]:O,[s("closeIconColorHover",r)]:ie,[s("closeIconColorPressed",r)]:de,[s("closeColorHover",r)]:he,[s("closeColorPressed",r)]:be}}=p.value,y=ue(_);return{"--n-font-weight-strong":oe,"--n-avatar-size-override":`calc(${j} - 8px)`,"--n-bezier":z,"--n-border-radius":w,"--n-border":ce,"--n-close-icon-size":ne,"--n-close-color-pressed":be,"--n-close-color-hover":he,"--n-close-border-radius":ee,"--n-close-icon-color":O,"--n-close-icon-color-hover":ie,"--n-close-icon-color-pressed":de,"--n-close-icon-color-disabled":O,"--n-close-margin-top":y.top,"--n-close-margin-right":y.right,"--n-close-margin-bottom":y.bottom,"--n-close-margin-left":y.left,"--n-close-size":le,"--n-color":u||(o.value?re:ae),"--n-color-checkable":X,"--n-color-checked":J,"--n-color-checked-hover":Q,"--n-color-checked-pressed":Z,"--n-color-hover-checkable":Y,"--n-color-pressed-checkable":G,"--n-font-size":te,"--n-height":j,"--n-opacity-disabled":V,"--n-padding":P,"--n-text-color":b||se,"--n-text-color-checkable":K,"--n-text-color-checked":W,"--n-text-color-hover-checkable":q,"--n-text-color-pressed-checkable":A}}),g=m?N("tag",I(()=>{let r="";const{type:n,size:u,color:{color:b,textColor:z}={}}=e;return r+=n[0],r+=u[0],b&&(r+=`a${H(b)}`),z&&(r+=`b${H(z)}`),o.value&&(r+="c"),r}),h,e):void 0;return Object.assign(Object.assign({},k),{rtlEnabled:x,mergedClsPrefix:d,contentRef:l,mergedBordered:o,handleClick:i,handleCloseClick:C,cssVars:m?void 0:h,themeClass:g?.themeClass,onRender:g?.onRender})},render(){var e,l;const{mergedClsPrefix:o,rtlEnabled:d,closable:m,color:{borderColor:$}={},round:p,onRender:i,$slots:C}=this;i?.();const k=T(C.avatar,h=>h&&a("div",{class:`${o}-tag__avatar`},h)),x=T(C.icon,h=>h&&a("div",{class:`${o}-tag__icon`},h));return a("div",{class:[`${o}-tag`,this.themeClass,{[`${o}-tag--rtl`]:d,[`${o}-tag--strong`]:this.strong,[`${o}-tag--disabled`]:this.disabled,[`${o}-tag--checkable`]:this.checkable,[`${o}-tag--checked`]:this.checkable&&this.checked,[`${o}-tag--round`]:p,[`${o}-tag--avatar`]:k,[`${o}-tag--icon`]:x,[`${o}-tag--closable`]:m}],style:this.cssVars,onClick:this.handleClick,onMouseenter:this.onMouseenter,onMouseleave:this.onMouseleave},x||k,a("span",{class:`${o}-tag__content`,ref:"contentRef"},(l=(e=this.$slots).default)===null||l===void 0?void 0:l.call(e)),!this.checkable&&m?a(ze,{clsPrefix:o,class:`${o}-tag__close`,disabled:this.disabled,onClick:this.handleCloseClick,focusable:this.internalCloseFocusable,round:p,isButtonTag:this.internalCloseIsButtonTag,absolute:!0}):null,!this.checkable&&this.mergedBordered?a("div",{class:`${o}-tag__border`,style:{borderColor:$}}):null)}}),Pe=f([v("list",`
 --n-merged-border-color: var(--n-border-color);
 --n-merged-color: var(--n-color);
 --n-merged-color-hover: var(--n-color-hover);
 margin: 0;
 font-size: var(--n-font-size);
 transition:
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier),
 border-color .3s var(--n-bezier);
 padding: 0;
 list-style-type: none;
 color: var(--n-text-color);
 background-color: var(--n-merged-color);
 `,[c("show-divider",[v("list-item",[f("&:not(:last-child)",[t("divider",`
 background-color: var(--n-merged-border-color);
 `)])])]),c("clickable",[v("list-item",`
 cursor: pointer;
 `)]),c("bordered",`
 border: 1px solid var(--n-merged-border-color);
 border-radius: var(--n-border-radius);
 `),c("hoverable",[v("list-item",`
 border-radius: var(--n-border-radius);
 `,[f("&:hover",`
 background-color: var(--n-merged-color-hover);
 `,[t("divider",`
 background-color: transparent;
 `)])])]),c("bordered, hoverable",[v("list-item",`
 padding: 12px 20px;
 `),t("header, footer",`
 padding: 12px 20px;
 `)]),t("header, footer",`
 padding: 12px 0;
 box-sizing: border-box;
 transition: border-color .3s var(--n-bezier);
 `,[f("&:not(:last-child)",`
 border-bottom: 1px solid var(--n-merged-border-color);
 `)]),v("list-item",`
 position: relative;
 padding: 12px 0; 
 box-sizing: border-box;
 display: flex;
 flex-wrap: nowrap;
 align-items: center;
 transition:
 background-color .3s var(--n-bezier),
 border-color .3s var(--n-bezier);
 `,[t("prefix",`
 margin-right: 20px;
 flex: 0;
 `),t("suffix",`
 margin-left: 20px;
 flex: 0;
 `),t("main",`
 flex: 1;
 `),t("divider",`
 height: 1px;
 position: absolute;
 bottom: 0;
 left: 0;
 right: 0;
 background-color: transparent;
 transition: background-color .3s var(--n-bezier);
 pointer-events: none;
 `)])]),me(v("list",`
 --n-merged-color-hover: var(--n-color-hover-modal);
 --n-merged-color: var(--n-color-modal);
 --n-merged-border-color: var(--n-border-color-modal);
 `)),pe(v("list",`
 --n-merged-color-hover: var(--n-color-hover-popover);
 --n-merged-color: var(--n-color-popover);
 --n-merged-border-color: var(--n-border-color-popover);
 `))]),_e=Object.assign(Object.assign({},B.props),{size:{type:String,default:"medium"},bordered:Boolean,clickable:Boolean,hoverable:Boolean,showDivider:{type:Boolean,default:!0}}),U=F("n-list"),je=M({name:"List",props:_e,slots:Object,setup(e){const{mergedClsPrefixRef:l,inlineThemeDisabled:o,mergedRtlRef:d}=S(e),m=L("List",d,l),$=B("List","-list",Pe,Ce,e,l);D(U,{showDividerRef:E(e,"showDivider"),mergedClsPrefixRef:l});const p=I(()=>{const{common:{cubicBezierEaseInOut:C},self:{fontSize:k,textColor:x,color:h,colorModal:g,colorPopover:r,borderColor:n,borderColorModal:u,borderColorPopover:b,borderRadius:z,colorHover:P,colorHoverModal:_,colorHoverPopover:w}}=$.value;return{"--n-font-size":k,"--n-bezier":C,"--n-text-color":x,"--n-color":h,"--n-border-radius":z,"--n-border-color":n,"--n-border-color-modal":u,"--n-border-color-popover":b,"--n-color-modal":g,"--n-color-popover":r,"--n-color-hover":P,"--n-color-hover-modal":_,"--n-color-hover-popover":w}}),i=o?N("list",void 0,p,e):void 0;return{mergedClsPrefix:l,rtlEnabled:m,cssVars:o?void 0:p,themeClass:i?.themeClass,onRender:i?.onRender}},render(){var e;const{$slots:l,mergedClsPrefix:o,onRender:d}=this;return d?.(),a("ul",{class:[`${o}-list`,this.rtlEnabled&&`${o}-list--rtl`,this.bordered&&`${o}-list--bordered`,this.showDivider&&`${o}-list--show-divider`,this.hoverable&&`${o}-list--hoverable`,this.clickable&&`${o}-list--clickable`,this.themeClass],style:this.cssVars},l.header?a("div",{class:`${o}-list__header`},l.header()):null,(e=l.default)===null||e===void 0?void 0:e.call(l),l.footer?a("div",{class:`${o}-list__footer`},l.footer()):null)}}),Oe=M({name:"ListItem",slots:Object,setup(){const e=ke(U,null);return e||xe("list-item","`n-list-item` must be placed in `n-list`."),{showDivider:e.showDividerRef,mergedClsPrefix:e.mergedClsPrefixRef}},render(){const{$slots:e,mergedClsPrefix:l}=this;return a("li",{class:`${l}-list-item`},e.prefix?a("div",{class:`${l}-list-item__prefix`},e.prefix()):null,e.default?a("div",{class:`${l}-list-item__main`},e):null,e.suffix?a("div",{class:`${l}-list-item__suffix`},e.suffix()):null,this.showDivider&&a("div",{class:`${l}-list-item__divider`}))}});export{Me as N,je as a,Oe as b,Be as t};
