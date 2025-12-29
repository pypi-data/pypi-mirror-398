# !/usr/bin/env python3

__version__="3.2.5"

def __init__():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
    subparsers = parser.add_subparsers(title="subcommands", dest="subcommand", help="choose a subcommand:")
    subparsers.add_parser('cpp', help='[cpp] connector cpp')
    subparsers.add_parser('gpp', help='[gpp] connector gpp')
    subparsers.add_parser('g', help='[g] cli connector g')
    subparsers.add_parser('c', help='[c] gui connector c')
    subparsers.add_parser('v', help='[v] vision connector')
    subparsers.add_parser('k', help='[k] k-flux connector')
    subparsers.add_parser('m', help='[m] menu')
    subparsers.add_parser('a', help='[a] frontend (api)')
    subparsers.add_parser('b', help='[b] frontend (api)')
    subparsers.add_parser('z', help='[z] serve frontend')
    subparsers.add_parser('o', help='[o] org web mirror')
    subparsers.add_parser('i', help='[i] i/o web mirror')
    subparsers.add_parser('w', help='[w] page/container')
    subparsers.add_parser('l', help='[l] cli-style chat')
    subparsers.add_parser('y', help='[y] download comfy')
    subparsers.add_parser('n', help='[n] clone node')
    subparsers.add_parser('u', help='[u] get cutter')
    subparsers.add_parser('p', help='[p] take pack')
    subparsers.add_parser('p1', help='[p1] take framepack')
    subparsers.add_parser('p2', help='[p2] take packpack')
    subparsers.add_parser('r', help='[r] metadata reader')
    subparsers.add_parser('r2', help='[r2] metadata fast reader')
    subparsers.add_parser('r3', help='[r3] tensor reader')
    subparsers.add_parser('r4', help='[r4] tensor info reader')
    subparsers.add_parser('r5', help='[r5] tensor reader (pt)')
    subparsers.add_parser('rm', help='[rm] tensor remover')
    subparsers.add_parser('rn', help='[rn] tensor renamer')
    subparsers.add_parser('ex', help='[ex] tensor extractor')
    subparsers.add_parser('e3', help='[e3] component extractor')
    subparsers.add_parser('e2', help='[e2] extractor (en/decoder)')
    subparsers.add_parser('e', help='[e] extractor (weight)')
    subparsers.add_parser('q', help='[q] tensor quantizor')
    subparsers.add_parser('q1', help='[q1] tensor quantizor (cpu)')
    subparsers.add_parser('q2', help='[q2] tensor quantizor (upscale)')
    subparsers.add_parser('q3', help='[q3] tensor quantizor (e5m2)')
    subparsers.add_parser('d', help='[d] divider (safetensors)')
    subparsers.add_parser('d2', help='[d2] divider (gguf)')
    subparsers.add_parser('m2', help='[m2] merger (gguf)')
    subparsers.add_parser('ma', help='[ma] merger (safetensors)')
    subparsers.add_parser('s', help='[s] splitter (checkpoint)')
    subparsers.add_parser('s1', help='[s1] splitter (uni/multi)')
    subparsers.add_parser('s0', help='[s0] splitter (d2 to d5)')
    subparsers.add_parser('s5', help='[s5] splitter (d5 else)')
    subparsers.add_parser('sx', help='[sx] splitter (d1 to dx)')
    subparsers.add_parser('sy', help='[sy] splitter (d2 else)')
    subparsers.add_parser('sr', help='[sr] seach and replace')
    subparsers.add_parser('la', help='[la] lora swapper')
    subparsers.add_parser('f', help='[f] tensor transfer')
    subparsers.add_parser('t', help='[t] tensor convertor')
    subparsers.add_parser('t3a', help='[t3a] tensor convertor (16)')
    subparsers.add_parser('t3b', help='[t3b] tensor convertor (u8)')
    subparsers.add_parser('t9m', help='[t9m] tensor convertor (mx)')
    subparsers.add_parser('t0', help='[t0] tensor convertor (zero)')
    subparsers.add_parser('t1', help='[t1] tensor convertor (alpha)')
    subparsers.add_parser('t2', help='[t2] tensor convertor (beta)')
    subparsers.add_parser('t3', help='[t3] tensor convertor (gamma)')
    subparsers.add_parser('t4', help='[t4] tensor convertor (delta)')
    subparsers.add_parser('t5', help='[t5] tensor convertor (epsilon)')
    subparsers.add_parser('t6', help='[t6] tensor convertor (zeta)')
    subparsers.add_parser('t7', help='[t7] tensor convertor (eta)')
    subparsers.add_parser('t8', help='[t8] tensor convertor (theta)')
    subparsers.add_parser('t9', help='[t9] tensor convertor (iota)')
    subparsers.add_parser('d9', help='[d9] tensor convertor (atoi)')
    subparsers.add_parser('d8', help='[d8] tensor convertor (dude)')
    subparsers.add_parser('d7', help='[d7] tensor convertor (plus)')
    subparsers.add_parser('d6', help='[d6] tensor convertor (t8xx)')
    subparsers.add_parser('d5', help='[d5] dimension 5 fixer (t8x)')
    subparsers.add_parser('p4', help='[p4] tensor convertor (4pth)')
    subparsers.add_parser('p5', help='[p5] tensor convertor (2pth)')
    subparsers.add_parser('p6', help='[p6] metadata formatter (pt)')
    subparsers.add_parser('sf', help='[sf] suffix adder')
    subparsers.add_parser('pf', help='[pf] prefix adder')
    subparsers.add_parser('pp', help='[pp] pdf analyzor pp')
    subparsers.add_parser('cp', help='[cp] pdf analyzor cp')
    subparsers.add_parser('ps', help='[ps] wav recognizor ps')
    subparsers.add_parser('cs', help='[cs] wav recognizor cs')
    subparsers.add_parser('cg', help='[cg] wav recognizor cg (api)')
    subparsers.add_parser('pg', help='[pg] wav recognizor pg (api)')
    subparsers.add_parser('vg', help='[vg] video generator')
    subparsers.add_parser('f5', help='[f5] fastvl5 (i2t)')
    subparsers.add_parser('f7', help='[f7] fastvl7 (cap)')
    subparsers.add_parser('f9', help='[f9] fastvl9 (itt)')
    subparsers.add_parser('g1', help='[g1] smart 1 (sol)')
    subparsers.add_parser('g3', help='[g3] oss-20b (gpt)')
    subparsers.add_parser('v1', help='[v1] video 1 (i2v)')
    subparsers.add_parser('v2', help='[v2] video 2 (t2v)')
    subparsers.add_parser('b1', help='[b1] bagel 1 (old)')
    subparsers.add_parser('b2', help='[b2] bagel 2 (a2a)')
    subparsers.add_parser('c1', help='[c1] voice 1 (new)')
    subparsers.add_parser('c2', help='[c2] voice 2 (t2c)')
    subparsers.add_parser('c3', help='[c3] voice 3 (mtl)')
    subparsers.add_parser('i2', help='[i2] image 2 (t2i)')
    subparsers.add_parser('f2', help='[f2] frame 2 (i2f)')
    subparsers.add_parser('s2', help='[s2] sound 2 (t2s)')
    subparsers.add_parser('o2', help='[o2] audio 2 (t2o)')
    subparsers.add_parser('n2', help='[n2] n-ocr 2 (n2m)')
    subparsers.add_parser('h2', help='[h2] higgs 2 (tts)')
    subparsers.add_parser('k1', help='[k1] kontx 1 (bot)')
    subparsers.add_parser('k2', help='[k2] kontx 2 (i2i)')
    subparsers.add_parser('k3', help='[k3] kontx 3 (i2i)')
    subparsers.add_parser('k4', help='[k4] kreas 4 (k4i)')
    subparsers.add_parser('k5', help='[k5] kreas 5 (k5i)')
    subparsers.add_parser('k6', help='[k6] kontx 6 (i6i)')
    subparsers.add_parser('k7', help='[k7] kreas 7 (k7i)')
    subparsers.add_parser('k8', help='[k8] kontx 8 (i8i)')
    subparsers.add_parser('q5', help='[q5] qweni 5 (qi5)')
    subparsers.add_parser('q6', help='[q6] qi-edit (i2i)')
    subparsers.add_parser('q7', help='[q7] qi-plus (i2i)')
    subparsers.add_parser('q0', help='[q0] qi-lite (i2i)')
    subparsers.add_parser('p0', help='[p0] qi-lit2 (i2i)')
    subparsers.add_parser('p9', help='[p9] qi-lit3 (i2i)')
    subparsers.add_parser('l2', help='[l2] lumina2 (t2i)')
    subparsers.add_parser('w2', help='[w2] wan-v 2 (t2v)')
    subparsers.add_parser('x2', help='[x2] ltx-v 2 (x2v)')
    subparsers.add_parser('m1', help='[m1] mochi 1 (m2v)')
    subparsers.add_parser('k0', help='[k0] kx-lite (i2i)')
    subparsers.add_parser('s3', help='[s3] sd-lite (t2i)')
    subparsers.add_parser('h3', help='[h3] holo1.5 (i2t)')
    subparsers.add_parser('h6', help='[h6] higgs 6 (tts)')
    subparsers.add_parser('s6', help='[s6] dia 1.6 (t2s)')
    subparsers.add_parser('f6', help='[f6] fastvlm (i2t)')
    subparsers.add_parser('v6', help='[v6] v-voice (v2s)')
    subparsers.add_parser('n3', help='[n3] docling (i2t)')
    subparsers.add_parser('q8', help='[q8] qi-plux (m2i)')
    subparsers.add_parser('q9', help='[q9] qi-pluz (m2i)')
    subparsers.add_parser('z1', help='[z1] z-image (t2i)')
    subparsers.add_parser('g2', help='[g2] gudio 2 (tts)')
    subparsers.add_parser('w9', help='[w9] istudio (img)')
    subparsers.add_parser('s8', help='[s8] sketch8 (skt)')
    subparsers.add_parser('s9', help='[s9] sketch9 (skt)')
    subparsers.add_parser('w8', help='[w8] op-sd3m (api)')
    subparsers.add_parser('w7', help='[w7] op-lma2 (api)')
    subparsers.add_parser('w6', help='[w6] op-flux (api)')
    subparsers.add_parser('b4', help='[b4] chatpig (web)')
    subparsers.add_parser('e4', help='[e4] chatpig (api)')
    subparsers.add_parser('e5', help='[e5] i-video (api)')
    subparsers.add_parser('e6', help='[e6] t-video (api)')
    subparsers.add_parser('e7', help='[e7] ig-read (api)')
    subparsers.add_parser('e8', help='[e8] ig-edit (api)')
    subparsers.add_parser('e9', help='[e9] mi-edit (api)')
    subparsers.add_parser('cu', help='[cu] computer use')
    subparsers.add_parser('vc', help='[vc] vibe code')
    args = parser.parse_args()
    if args.subcommand == 'm':
        from gguf_connector import m
    elif args.subcommand=='n':
        from gguf_connector import n
    elif args.subcommand=='f':
        from gguf_connector import f
    elif args.subcommand=='a':
        from gguf_connector import a
    elif args.subcommand=='b':
        from gguf_connector import b
    elif args.subcommand=='z':
        from gguf_connector import z
    elif args.subcommand=='p':
        from gguf_connector import p
    elif args.subcommand=='p1':
        from gguf_connector import p1
    elif args.subcommand=='p2':
        from gguf_connector import p2
    elif args.subcommand=="r":
        from gguf_connector import r
    elif args.subcommand=="r2":
        from gguf_connector import r2
    elif args.subcommand=="r3":
        from gguf_connector import r3
    elif args.subcommand=="r4":
        from gguf_connector import r4
    elif args.subcommand=="r5":
        from gguf_connector import r5
    elif args.subcommand=="rm":
        from gguf_connector import re1
    elif args.subcommand=="rn":
        from gguf_connector import re2
    elif args.subcommand=="ex":
        from gguf_connector import ex1
    elif args.subcommand=="e":
        from gguf_connector import e
    elif args.subcommand=="e2":
        from gguf_connector import e2
    elif args.subcommand=="e3":
        from gguf_connector import e3
    elif args.subcommand=="b4":
        from gguf_connector import b4
    elif args.subcommand=="e4":
        from gguf_connector import e4
    elif args.subcommand=="e5":
        from gguf_connector import e5
    elif args.subcommand=="e6":
        from gguf_connector import e6
    elif args.subcommand=="e7":
        from gguf_connector import e7
    elif args.subcommand=="e8":
        from gguf_connector import e8
    elif args.subcommand=="e9":
        from gguf_connector import e9
    elif args.subcommand=="s":
        from gguf_connector import s
    elif args.subcommand=="s1":
        from gguf_connector import s1
    elif args.subcommand=="s0":
        from gguf_connector import s0
    elif args.subcommand=="s5":
        from gguf_connector import s5
    elif args.subcommand=="s6":
        from gguf_connector import s6
    elif args.subcommand=="s8":
        from gguf_connector import s8
    elif args.subcommand=="s9":
        from gguf_connector import s9
    elif args.subcommand=="s3":
        from gguf_connector import s3
    elif args.subcommand=="sx":
        from gguf_connector import sx
    elif args.subcommand=="sy":
        from gguf_connector import sy
    elif args.subcommand=='sf':
        from gguf_connector import sf
    elif args.subcommand=='sr':
        from gguf_connector import sr
    elif args.subcommand=='la':
        from gguf_connector import sr2
    elif args.subcommand=='pf':
        from gguf_connector import pf
    elif args.subcommand=="k":
        from gguf_connector import k
    elif args.subcommand=="i":
        from gguf_connector import i
    elif args.subcommand=="o":
        from gguf_connector import o
    elif args.subcommand=="u":
        from gguf_connector import u
    elif args.subcommand=="v":
        from gguf_connector import v
    elif args.subcommand=="vg":
        from gguf_connector import vg
    elif args.subcommand=="v1":
        from gguf_connector import vg2
    elif args.subcommand=="v2":
        from gguf_connector import v2
    elif args.subcommand=="v6":
        from gguf_connector import v6
    elif args.subcommand=="w9":
        from gguf_connector import w9
    elif args.subcommand=="w8":
        from gguf_connector import w8
    elif args.subcommand=="w7":
        from gguf_connector import w7
    elif args.subcommand=="w6":
        from gguf_connector import w6
    elif args.subcommand=="w2":
        from gguf_connector import w2
    elif args.subcommand=="x2":
        from gguf_connector import x2
    elif args.subcommand=="i2":
        from gguf_connector import i2
    elif args.subcommand=="c1":
        from gguf_connector import c1
    elif args.subcommand=="c2":
        from gguf_connector import c2
    elif args.subcommand=="c3":
        from gguf_connector import c3
    elif args.subcommand=="g1":
        from gguf_connector import g1
    elif args.subcommand=="g2":
        from gguf_connector import g2
    elif args.subcommand=="g3":
        from gguf_connector import g3
    elif args.subcommand=="h6":
        from gguf_connector import h6
    elif args.subcommand=="h2":
        from gguf_connector import h2
    elif args.subcommand=="o2":
        from gguf_connector import o2
    elif args.subcommand=="s2":
        from gguf_connector import s2
    elif args.subcommand=="f2":
        from gguf_connector import f2
    elif args.subcommand=="f5":
        from gguf_connector import f5
    elif args.subcommand=="f6":
        from gguf_connector import f6
    elif args.subcommand=="f7":
        from gguf_connector import f7
    elif args.subcommand=="f9":
        from gguf_connector import f9
    elif args.subcommand=="h3":
        from gguf_connector import h3
    elif args.subcommand=="n2":
        from gguf_connector import n2
    elif args.subcommand=="n3":
        from gguf_connector import n3
    elif args.subcommand=="k0":
        from gguf_connector import k0
    elif args.subcommand=="k1":
        from gguf_connector import k1
    elif args.subcommand=="k2":
        from gguf_connector import k2
    elif args.subcommand=="k3":
        from gguf_connector import k3
    elif args.subcommand=="k4":
        from gguf_connector import k4
    elif args.subcommand=="k5":
        from gguf_connector import k5
    elif args.subcommand=="k6":
        from gguf_connector import k6
    elif args.subcommand=="k7":
        from gguf_connector import k7
    elif args.subcommand=="k8":
        from gguf_connector import k8
    elif args.subcommand=="q5":
        from gguf_connector import q5
    elif args.subcommand=="q6":
        from gguf_connector import q6
    elif args.subcommand=="q7":
        from gguf_connector import q7
    elif args.subcommand=="q8":
        from gguf_connector import q8
    elif args.subcommand=="q9":
        from gguf_connector import q9
    elif args.subcommand=="q0":
        from gguf_connector import q0
    elif args.subcommand=="z1":
        from gguf_connector import z1
    elif args.subcommand=="p0":
        from gguf_connector import p0
    elif args.subcommand=="p9":
        from gguf_connector import p9
    elif args.subcommand=="l2":
        from gguf_connector import l2
    elif args.subcommand=="b1":
        from gguf_connector import b1
    elif args.subcommand=="b2":
        from gguf_connector import b2
    elif args.subcommand=="l":
        from gguf_connector import l
    elif args.subcommand=="w":
        from gguf_connector import w
    elif args.subcommand=="y":
        from gguf_connector import y
    elif args.subcommand=="t":
        from gguf_connector import t
    elif args.subcommand=="t0":
        from gguf_connector import t0
    elif args.subcommand=="t1":
        from gguf_connector import t1
    elif args.subcommand=="t2":
        from gguf_connector import t2
    elif args.subcommand=="t3":
        from gguf_connector import t3
    elif args.subcommand=="t3a":
        from gguf_connector import t3a
    elif args.subcommand=="t3b":
        from gguf_connector import t3b
    elif args.subcommand=="t4":
        from gguf_connector import t4
    elif args.subcommand=="t5":
        from gguf_connector import t5
    elif args.subcommand=="t6":
        from gguf_connector import t6
    elif args.subcommand=="t7":
        from gguf_connector import t7
    elif args.subcommand=="t8":
        from gguf_connector import t8
    elif args.subcommand=="t9":
        from gguf_connector import t9
    elif args.subcommand=="t9m":
        from gguf_connector import t9m
    elif args.subcommand=="d9":
        from gguf_connector import d9
    elif args.subcommand=="d8":
        from gguf_connector import d8
    elif args.subcommand=="d7":
        from gguf_connector import d7
    elif args.subcommand=="d6":
        from gguf_connector import d6
    elif args.subcommand=="d5":
        from gguf_connector import d5
    elif args.subcommand=='p6':
        from gguf_connector import p6
    elif args.subcommand=='p5':
        from gguf_connector import p5
    elif args.subcommand=='p4':
        from gguf_connector import p4
    elif args.subcommand=="q":
        from gguf_connector import q
    elif args.subcommand=="q1":
        from gguf_connector import q1
    elif args.subcommand=="q2":
        from gguf_connector import q2
    elif args.subcommand=="q3":
        from gguf_connector import q3
    elif args.subcommand=="d":
        from gguf_connector import d
    elif args.subcommand=="d2":
        from gguf_connector import d2
    elif args.subcommand=="m1":
        from gguf_connector import m1
    elif args.subcommand=="m2":
        from gguf_connector import m2
    elif args.subcommand=="ma":
        from gguf_connector import ma
    elif args.subcommand=="cg":
        from gguf_connector import cg
    elif args.subcommand=="pg":
        from gguf_connector import pg
    elif args.subcommand=="cs":
        from gguf_connector import cs
    elif args.subcommand=="ps":
        from gguf_connector import ps
    elif args.subcommand=="cp":
        from gguf_connector import cp
    elif args.subcommand=="pp":
        from gguf_connector import pp
    elif args.subcommand=="c":
        from gguf_connector import c
    elif args.subcommand=="cpp":
        from gguf_connector import cpp
    elif args.subcommand=="g":
        from gguf_connector import g
    elif args.subcommand=="gpp":
        from gguf_connector import gpp
    elif args.subcommand=="vc":
        from gguf_connector import vc
    elif args.subcommand=="cu":
        from gguf_connector import cu