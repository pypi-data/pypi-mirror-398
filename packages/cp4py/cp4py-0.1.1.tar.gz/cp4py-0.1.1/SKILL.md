# cp4py

## 概要

- CP言語と処理系
- 処理系のバックエンドは既存の cpoptimizer, gurobi, scip, z3, ortools など
- 処理系は言語からバックエンドの API への変換を行う

## 言語のイメージ

前置記法+json
変数，制約の区分はなく，接頭辞をみてtranslatorがapiをcall

An example:

def magicSquare3x3(x=Var("x")):
    for i in range(3):
        for j in range(3):
            yield ["int", x(i,j), 1, 9]
    xx = [ x(i,j) for i in range(3) for j in range(3) ]
    yield ["alldifferent", *xx]
    for i in range(3):
        yield ["==", ["+", x(i,0), x(i,1), x(i,2)], 15]
    for j in range(3):
        yield ["==", ["+", x(0,j), x(1,j), x(2,j)], 15]
    yield ["==", ["+", x(0,0), x(1,1), x(2,2)], 15]
    yield ["==", ["+", x(0,2), x(1,1), x(2,0)], 15]

## 開発方法

- t-wada の TDD

## 実装計画

phase が終わる度にレビューをユーザーに依頼

### Phase 1 言語

- 線形比較制約の選言の連言
- 目的関数

### Phase 2 translator for ortools

### Phase 3 translator for z3

### Phase 4 translator for scip
