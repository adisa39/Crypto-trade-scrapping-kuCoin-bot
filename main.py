from config1 import kc_client
import requests
import pandas as pd
import time


def booked_display(side):
    df = pd.DataFrame(side, columns=['price', 'quantity'])
    df.quantity = df.quantity.astype(float)
    df['percent'] = (df['quantity'] / df['quantity'].sum()) * 100
    max_percent = df.loc[df['percent'].idxmax()]
    # print(f"maximum percentage - {max_percent} \n")
    # print(df)
    return max_percent


def set_price(cur_price, offset, for_sale):
    a, b = cur_price.split('.')
    if for_sale:
        dec = int(b) - offset
    else:
        dec = int(b) + offset

    if b.startswith('000'):
        new_price = a + '.000' + str(dec)
    elif b.startswith('00'):
        new_price = a + '.00' + str(dec)
    elif b.startswith('0'):
        new_price = a + '.0' + str(dec)
    else:
        new_price = a + '.' + str(dec)
    return new_price


def new_order(symbol, max_price, amount, side, for_sale=False):
    order_price = set_price(max_price, 1, for_sale)    
    order_size = round((amount / float(order_price)), 3)
    print(f"\norder size - {order_size}  order price ${order_price}")    

    try:    
        # order_id = limit_buy_token(COIN_NAME, coin_details, float(AMOUNT), float(buy_price))
        order_id = kc_client.create_limit_order(symbol, side, price=str(order_price), size=str(order_size)) 
        # print(f"order id - {order_id}")
        if order_id:
            return max_price, order_id['orderId']
            
    except Exception as ex:
        print(str(ex) + "  \r'retrying...'")


def compute_max_price(symbol, for_20):
    booked = kc_client.get_order_book(symbol, for_20)
    
    bids = booked["bids"]    
    max_bid = booked_display(bids)
    bid_max_price = str(round(float(max_bid['price']), len(coin_details['priceIncrement'])-2))    

    asks = booked["asks"]
    max_ask = booked_display(asks)
    ask_max_price = str(round(float(max_ask['price']), len(coin_details['priceIncrement'])-2))
    print(f"\rRefreshing... max bid - ${bid_max_price}   max ask - ${ask_max_price}", end=" ")

    return bid_max_price, ask_max_price


def main(COIN_NAME, AMOUNT, for_20):
#     COIN_NAME = "KLUB"
    SYMBOL = COIN_NAME+'-USDT'
    # AMOUNT = 2    

    max_bid_price, max_ask_price = compute_max_price(SYMBOL, for_20)
    buy_price, buy_order_id = new_order(SYMBOL, max_bid_price, AMOUNT, kc_client.SIDE_BUY)
    print(f"Initial Buy order created - {buy_order_id}")
    sell_price = ""

    while True:
        max_bid_price, max_ask_price = compute_max_price(SYMBOL, for_20)
        order_status = kc_client.get_order(buy_order_id)

        # CREATE NEW SELL ORDER and BUY ORDER IF PREVIUS ORDER IS FILLED
        if not order_status['isActive'] and not order_status['cancelExist']:

            # check if max_ask_price is not below the buy_price to avoid losses
            if float(buy_price) > float(max_ask_price):
                max_ask_price = buy_price

            sell_price, sell_order_id = new_order(SYMBOL, max_ask_price, AMOUNT, kc_client.SIDE_SELL, for_sale=True)
            print(f"previous order Filled and New Sell order created  ${sell_order_id} \n") 

            buy_price, buy_order_id = new_order(SYMBOL, max_bid_price, AMOUNT, kc_client.SIDE_BUY)
            print(f"previous order Filled and New Buy order created  ${buy_order_id} \n")
        
        else:
            # cancel order and re-book the order
            if max_bid_price != buy_price:
                kc_client.cancel_order(buy_order_id)                
                buy_price, buy_order_id = new_order(SYMBOL, max_bid_price, AMOUNT, kc_client.SIDE_BUY)
                print(f"\n New Buy order created - {buy_order_id}")

            # cancel order and re-book the order
            if max_ask_price != sell_price and sell_price != "":
                kc_client.cancel_order(sell_order_id)
                if float(buy_price) > float(max_ask_price):
                    max_ask_price = buy_price
                sell_price, sell_order_id = new_order(SYMBOL, max_ask_price, AMOUNT, kc_client.SIDE_SELL, for_sale=True)
                print(f"\n New Sell order created - {sell_order_id}")

        time.sleep(30)


if __name__=="__main__":
    COIN_NAME = "KLUB"
    USDT_AMOUNT = 2
    for_20 = True
    coin_details = requests.request('GET', 'https://api.kucoin.com' + f'/api/v1/symbols/{COIN_NAME}-USDT').json()[
            'data']

    main(COIN_NAME, USDT_AMOUNT, for_20)